#!/usr/bin/env python3
import os
from pathlib import Path

def check_additive():
    print("Checking additive isolated components...")
    checks = {
        "Config Template Gen": Path("scripts/generate_config_template.py").exists(),
        "API Examples": Path("examples/api/success_chat.json").exists(),
        "Failure Fixtures": Path("fixtures/failures/duplicate_model_ids.json").exists(),
        "Schemas": Path("schemas/registry_entry.schema.json").exists(),
        "Evidence Formatter": Path("scripts/format_evidence.py").exists()
    }
    
    all_ok = True
    for name, exists in checks.items():
        status = "OK" if exists else "MISSING"
        print(f"{name}: {status}")
        if not exists: all_ok = False
        
    print(f"\nOverall Additive Check: {'PASSED' if all_ok else 'FAILED'}")
    # Note: Merge point -> Import into scripts/doctor.py `run_doctor()` Phase 5.

if __name__ == "__main__":
    check_additive()
