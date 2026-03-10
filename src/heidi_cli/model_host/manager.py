from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import psutil
from ..shared.config import ConfigLoader, ModelConfig
from ..token_tracking.models import get_token_database, TokenUsage

logger = logging.getLogger("heidi.model_host")

# Lazy imports for transformers
torch = None
transformers = None


def _lazy_imports():
    """Lazy load torch and transformers."""
    global torch, transformers
    if transformers is None:
        import torch
        import transformers
        # Fixed: Remove redundant assignment
        return torch, transformers
    return torch, transformers


class ModelManager:
    """Manages local model loading and routing."""
    
    def __init__(self):
        self.config = ConfigLoader.load()
        self.loaded_models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {m.id: m for m in self.config.models}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load model from registry
        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.model_path: Optional[Path] = None
        
        # Token tracking
        self.token_db = get_token_database()
        self.default_session_id = str(uuid.uuid4())
        
        # Generation configuration
        self.generation_config = {
            "max_new_tokens": getattr(self.config, 'max_new_tokens', 128),
            "temperature": getattr(self.config, 'temperature', 0.7),
            "do_sample": getattr(self.config, 'do_sample', True),
            "top_p": getattr(self.config, 'top_p', 0.9),
            "top_k": getattr(self.config, 'top_k', 50),
        }
        
        # Resource limits
        self.max_memory_gb = getattr(self.config, 'max_memory_gb', 8)
        self.max_concurrent_requests = getattr(self.config, 'max_concurrent_requests', 10)
        self._active_requests = 0
        
        # Security settings
        self.allowed_model_paths = getattr(self.config, 'allowed_model_paths', [
            Path.home() / ".local" / "heidi-engine",
            Path("models"),
            Path("state/registry")
        ])
        
        self._load_model_from_registry()
    
    def _validate_model_path(self, model_path: Path) -> bool:
        """Validate model path for security."""
        try:
            # Resolve absolute path
            abs_path = model_path.resolve()
            
            # Check if path is within allowed directories
            for allowed_path in self.allowed_model_paths:
                if allowed_path.exists():
                    try:
                        if abs_path.is_relative_to(allowed_path.resolve()):
                            return True
                    except AttributeError:
                        # Fallback for older Python versions
                        if str(abs_path).startswith(str(allowed_path.resolve())):
                            return True
            
            logger.warning(f"Model path not in allowed directories: {abs_path}")
            return False
        except Exception as e:
            logger.error(f"Error validating model path: {e}")
            return False
    
    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within limits."""
        try:
            memory_info = psutil.virtual_memory()
            used_gb = memory_info.used / (1024**3)
            
            if used_gb > self.max_memory_gb:
                logger.warning(f"Memory usage {used_gb:.2f}GB exceeds limit {self.max_memory_gb}GB")
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return True  # Allow on error
    
    def _load_model_from_registry(self):
        """Load model from active_stable in registry.json."""
        with self._lock:
            try:
                registry_path = Path("state/registry/registry.json")
                if not registry_path.exists():
                    logger.warning("Registry not found, model not loaded")
                    return
                
                with open(registry_path) as f:
                    registry = json.load(f)
                
                active_version = registry.get("active_stable")
                if not active_version:
                    logger.warning("No active_stable version in registry")
                    return
                
                versions = registry.get("versions", {})
                version_info = versions.get(active_version)
                if not version_info:
                    logger.warning(f"Version {active_version} not found in registry versions")
                    return
                
                model_path = Path(version_info.get("path", ""))
                if not model_path.exists():
                    logger.warning(f"Model path does not exist: {model_path}")
                    return
                
                # Security validation
                if not self._validate_model_path(model_path):
                    logger.error(f"Security validation failed for model path: {model_path}")
                    return
                
                # Check memory before loading
                if not self._check_memory_usage():
                    logger.error("Insufficient memory to load model")
                    return
                
                self.model_path = model_path
                logger.info(f"Loading model from: {model_path}")
                
                # Lazy import transformers
                torch, transformers = _lazy_imports()
                
                # Load tokenizer and model
                self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                    str(model_path),
                    trust_remote_code=True,
                    local_files_only=True  # Security: only load local files
                )
                self.model = transformers.AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    device_map="auto",
                    torch_dtype=torch.float16,
                    low_cpu_memory_usage=True,
                    trust_remote_code=True,
                    local_files_only=True  # Security: only load local files
                )
                
                # Set pad token
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token_id
                
                logger.info(f"Model loaded successfully: {active_version}")
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.tokenizer = None
                self.model = None
                self.model_path = None

    def list_models(self) -> List[Dict[str, Any]]:
        """List routable models for /v1/models."""
        models = []
        
        # Add registry versions
        try:
            registry_path = Path("state/registry/registry.json")
            if registry_path.exists():
                with open(registry_path) as f:
                    registry = json.load(f)
                
                versions = registry.get("versions", {})
                for version_id, version_info in versions.items():
                    models.append({
                        "id": version_id,
                        "object": "model",
                        "created": 1677610602,
                        "owned_by": "heidi-local",
                        "permission": [],
                        "root": version_info.get("path", ""),
                        "parent": None,
                        "channel": version_info.get("channel", "unknown"),
                    })
        except Exception as e:
            logger.error(f"Failed to read registry for list_models: {e}")
        
        # Also add configured models
        for mid, cfg in self.model_configs.items():
            models.append({
                "id": mid,
                "object": "model",
                "created": 1677610602,
                "owned_by": "heidi-local",
                "permission": [],
                "root": str(cfg.path),
                "parent": None,
            })
        
        return models

    async def get_response(self, model_id: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Route request to the correct model and get response."""
        session_id = kwargs.pop('session_id', self.default_session_id)
        user_id = kwargs.pop('user_id', 'default')
        request_start_time = kwargs.pop('request_start_time', None)
        
        with self._lock:
            # Check concurrent request limit
            if self._active_requests >= self.max_concurrent_requests:
                logger.warning(f"Too many concurrent requests: {self._active_requests}")
                return self._fallback_response(model_id, messages, "Server overloaded")
            
            self._active_requests += 1
        
        try:
            # Check if model is loaded
            if self.model is None or self.tokenizer is None:
                logger.warning("Model not loaded, using fallback response")
                return self._fallback_response(model_id, messages, "Model not loaded")
            
            # Check memory usage
            if not self._check_memory_usage():
                logger.warning("High memory usage, using fallback response")
                return self._fallback_response(model_id, messages, "High memory usage")
            
            # Merge generation config with request parameters
            gen_config = self.generation_config.copy()
            gen_config.update({k: v for k, v in kwargs.items() if k in gen_config})
            
            # Use chat template
            inputs = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                return_tensors="pt"
            )
            
            # Move inputs to same device as model
            device = next(self.model.parameters()).device
            inputs = inputs.to(device)
            
            # Generate response
            outputs = self.model.generate(
                inputs,
                max_new_tokens=gen_config["max_new_tokens"],
                do_sample=gen_config["do_sample"],
                temperature=gen_config["temperature"],
                top_p=gen_config.get("top_p", 0.9),
                top_k=gen_config.get("top_k", 50),
                pad_token_id=self.tokenizer.eos_token_id,
            )
            
            # Decode only the new tokens (skip input)
            input_length = inputs.shape[1]
            response_tokens = outputs[0][input_length:]
            response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            
            # Create response
            response = {
                "id": f"chatcmpl-{model_id}",
                "object": "chat.completion",
                "created": 1677610602,
                "model": model_id,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": input_length,
                    "completion_tokens": len(response_tokens),
                    "total_tokens": input_length + len(response_tokens)
                }
            }
            
            # Record token usage
            self._record_token_usage(
                model_id=model_id,
                session_id=session_id,
                user_id=user_id,
                prompt_tokens=input_length,
                completion_tokens=len(response_tokens),
                total_tokens=input_length + len(response_tokens),
                request_type="chat_completion",
                metadata={
                    "request_start_time": request_start_time.isoformat() if request_start_time else None,
                    "generation_config": gen_config,
                    "model_path": str(self.model_path) if self.model_path else None
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error during model inference: {e}")
            return self._fallback_response(model_id, messages, f"Inference error: {str(e)}")
        finally:
            with self._lock:
                self._active_requests -= 1
    
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count using simple heuristics when tokenizer unavailable."""
        if not text:
            return 0
        
        # Simple heuristic: average token is ~4 characters
        # Add some buffer for special tokens
        estimated_tokens = len(text) // 4 + len(text.split()) // 2
        return max(1, estimated_tokens)
    
    def _fallback_response(self, model_id: str, messages: List[Dict[str, str]], error_msg: str = "") -> Dict[str, Any]:
        """Fallback response when model is not available."""
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        response_text = f"[Local {model_id} Response to: {prompt[:50]}...]"
        if error_msg:
            response_text = f"[Model unavailable: {error_msg}]"
        
        # Proper token counting
        prompt_tokens = self._estimate_token_count(prompt)
        completion_tokens = self._estimate_token_count(response_text)
        
        return {
            "id": f"chatcmpl-{model_id}",
            "object": "chat.completion",
            "created": 1677610602,
            "model": model_id,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }
    
    def unload_model(self):
        """Unload model and free memory."""
        with self._lock:
            try:
                if self.model is not None:
                    # Move model to CPU first
                    if hasattr(self.model, 'cpu'):
                        self.model.cpu()
                    
                    # Clear references
                    del self.model
                    self.model = None
                
                if self.tokenizer is not None:
                    del self.tokenizer
                    self.tokenizer = None
                
                self.model_path = None
                
                # Force garbage collection
                import gc
                gc.collect()
                
                # Clear CUDA cache if available
                try:
                    torch = _lazy_imports()[0]
                    if torch and torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass
                
                logger.info("Model unloaded successfully")
                
            except Exception as e:
                logger.error(f"Error unloading model: {e}")
    
    def reload_model(self):
        """Reload model from registry."""
        self.unload_model()
        self._load_model_from_registry()
    
    def _record_token_usage(
        self,
        model_id: str,
        session_id: str,
        user_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        request_type: str = "chat_completion",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record token usage to database."""
        try:
            # Get cost configuration
            cost_config = self.token_db.get_cost_config("local", model_id)
            
            # Calculate cost
            if cost_config:
                cost_usd = cost_config.calculate_cost(prompt_tokens, completion_tokens)
            else:
                # Default cost estimation for local models
                cost_usd = 0.0  # Free for local models
            
            # Create usage record
            usage = TokenUsage(
                model_id=model_id,
                session_id=session_id,
                user_id=user_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                request_type=request_type,
                model_provider="local",
                cost_usd=cost_usd,
                metadata=metadata
            )
            
            # Save to database
            self.token_db.record_usage(usage)
            
            logger.debug(f"Recorded token usage: {total_tokens} tokens for {model_id}")
            
        except Exception as e:
            logger.error(f"Failed to record token usage: {e}")
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource usage status."""
        try:
            memory = psutil.virtual_memory()
            return {
                "memory_used_gb": memory.used / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "memory_percent": memory.percent,
                "active_requests": self._active_requests,
                "max_concurrent_requests": self.max_concurrent_requests,
                "model_loaded": self.model is not None,
                "model_path": str(self.model_path) if self.model_path else None,
                "session_id": self.default_session_id,
            }
        except Exception as e:
            logger.error(f"Error getting resource status: {e}")
            return {"error": str(e)}


# Global manager instance
manager = ModelManager()
