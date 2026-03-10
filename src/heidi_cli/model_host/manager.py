from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..shared.config import ConfigLoader, ModelConfig

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
        torch = torch
        transformers = transformers


class ModelManager:
    """Manages local model loading and routing."""
    
    def __init__(self):
        self.config = ConfigLoader.load()
        self.loaded_models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {m.id: m for m in self.config.models}
        
        # Load model from registry
        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.model_path: Optional[Path] = None
        self._load_model_from_registry()
    
    def _load_model_from_registry(self):
        """Load model from active_stable in registry.json."""
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
            
            self.model_path = model_path
            logger.info(f"Loading model from: {model_path}")
            
            # Lazy import transformers
            _lazy_imports()
            
            # Load tokenizer and model
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                str(model_path),
                trust_remote_code=True
            )
            self.model = transformers.AutoModelForCausalLM.from_pretrained(
                str(model_path),
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_memory_usage=True,
                trust_remote_code=True
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
        # Check if model is loaded
        if self.model is None or self.tokenizer is None:
            # Fallback to placeholder response
            logger.warning("Model not loaded, using fallback response")
            return self._fallback_response(model_id, messages)
        
        try:
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
                max_new_tokens=128,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            
            # Decode only the new tokens (skip input)
            input_length = inputs.shape[1]
            response_tokens = outputs[0][input_length:]
            response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            
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
                    "prompt_tokens": input_length,
                    "completion_tokens": len(response_tokens),
                    "total_tokens": input_length + len(response_tokens)
                }
            }
            
        except Exception as e:
            logger.error(f"Error during model inference: {e}")
            return self._fallback_response(model_id, messages)
    
    def _fallback_response(self, model_id: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Fallback response when model is not available."""
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        response_text = f"[Local {model_id} Response to: {prompt[:50]}...]"
        
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
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split())
            }
        }


# Global manager instance
manager = ModelManager()
