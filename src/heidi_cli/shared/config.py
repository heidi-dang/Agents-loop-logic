from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, model_validator


def find_project_root() -> Path:
    """Find the project root by walking up for pyproject.toml."""
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd().resolve()


def get_default_state_root() -> Path:
    """Get the default state root for the learning suite."""
    env_root = os.environ.get("HEIDI_STATE_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return find_project_root() / "state"


class ModelConfig(BaseModel):
    id: str
    path: Path
    backend: str = "transformers"
    device: str = "auto"
    precision: str = "auto"
    max_tokens: Optional[int] = None
    max_context: Optional[int] = None

    def model_dump(self, **kwargs):
        # Convert Path objects to strings for JSON serialization
        d = super().model_dump(**kwargs)
        if isinstance(d.get("path"), Path):
            d["path"] = str(d["path"])
        return d


class SuiteConfig(BaseModel):
    suite_enabled: bool = True
    data_root: Path = Field(default_factory=get_default_state_root)
    model_host_enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    models: List[ModelConfig] = []
    backend_engine: str = "transformers"
    base_model_path: Optional[Path] = None
    request_timeout: int = 60
    max_memory_gb: int = 32
    max_concurrent_requests: int = 10

    memory_enabled: bool = True
    memory_sqlite_path: Optional[Path] = None
    vector_index_path: Optional[Path] = None
    embedding_model: str = "all-MiniLM-L6-v2"

    constitution_enabled: bool = True
    reflection_enabled: bool = True
    reward_enabled: bool = True
    strategy_ranking_enabled: bool = True

    event_logging_enabled: bool = True
    dataset_export_enabled: bool = True

    full_retraining_enabled: bool = True
    retrain_threshold: float = 0.8
    retrain_schedule: str = "0 0 * * *"

    promotion_policy: str = "beat_stable"
    rollback_policy: str = "auto_on_regression"
    retention_policy: str = "keep_last_5"

    log_level: str = "info"

    @property
    def state_dirs(self) -> Dict[str, Path]:
        root = self.data_root
        return {
            "config": root / "config",
            "memory": root / "memory",
            "events": root / "events",
            "datasets_raw": root / "datasets" / "raw",
            "datasets_curated": root / "datasets" / "curated",
            "models_stable": root / "models" / "stable" / "versions",
            "models_candidate": root / "models" / "candidate" / "versions",
            "models_experimental": root / "models" / "experimental" / "versions",
            "registry": root / "registry",
            "logs": root / "logs",
            "evals": root / "evals",
        }

    def ensure_dirs(self):
        for path in self.state_dirs.values():
            path.mkdir(parents=True, exist_ok=True)

    def model_dump(self, **kwargs):
        # Convert Path objects to strings for JSON serialization
        d = super().model_dump(**kwargs)

        if isinstance(d.get("data_root"), Path):
            d["data_root"] = str(d["data_root"])

        if isinstance(d.get("base_model_path"), Path):
            d["base_model_path"] = str(d["base_model_path"])

        if isinstance(d.get("models"), list):
            for model in d["models"]:
                if isinstance(model.get("path"), Path):
                    model["path"] = str(model["path"])

        if isinstance(d.get("memory_sqlite_path"), Path):
            d["memory_sqlite_path"] = str(d["memory_sqlite_path"])

        if isinstance(d.get("vector_index_path"), Path):
            d["vector_index_path"] = str(d["vector_index_path"])

        return d


class ConfigLoader:
    @staticmethod
    def load() -> SuiteConfig:
        default_root = get_default_state_root()
        config_path = default_root / "config" / "suite.json"

        env_config = os.environ.get("HEIDI_SUITE_CONFIG")
        if env_config:
            config_path = Path(env_config)

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    config = SuiteConfig(**data)
            except Exception as e:
                print(f"Warning: Failed to load suite config from {config_path}: {e}")
                config = SuiteConfig()
        else:
            config = SuiteConfig()

        # Env overrides
        for field in SuiteConfig.model_fields:
            env_key = f"HEIDI_SUITE_{field.upper()}"
            env_val = os.environ.get(env_key)
            if env_val:
                try:
                    if field == "models":
                        # Special handling for models JSON list via env if needed
                        continue

                    target_type = SuiteConfig.model_fields[field].annotation
                    if target_type is bool:
                        setattr(config, field, env_val.lower() in ("true", "1", "yes"))
                    elif target_type is int:
                        setattr(config, field, int(env_val))
                    elif target_type is float:
                        setattr(config, field, float(env_val))
                    elif target_type is Path:
                        setattr(config, field, Path(env_val))
                    else:
                        setattr(config, field, env_val)
                except Exception as e:
                    print(f"Warning: Failed to parse env {env_key}={env_val}: {e}")

        return config
