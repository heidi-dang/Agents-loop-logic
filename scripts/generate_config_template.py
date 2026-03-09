#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

TEMPLATE = {
    "suite_enabled": True,
    "data_root": "/absolute/path/to/data",
    "model_host_enabled": True,
    "models": [
        {
            "id": "qwen-coder-7b",
            "path": "/path/to/models/qwen",
            "context_length": 8192,
            "backend": "llama.cpp"
        }
    ],
    "memory_sqlite_path": "/path/to/memory.db",
    "vector_index_path": "/path/to/vector.idx",
    "full_retraining_enabled": False,
    "promotion_policy": "beat_stable"
}

def generate_template(output_path: str):
    path = Path(output_path)
    # Basic validation dummy check
    assert "models" in TEMPLATE and isinstance(TEMPLATE["models"], list)
    with open(path, "w") as f:
        json.dump(TEMPLATE, f, indent=2)
    print(f"Generated clean config template at {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate learning suite config template.")
    parser.add_argument("--output", default="suite.template.json", help="Output path")
    args = parser.parse_args()
    generate_template(args.output)
