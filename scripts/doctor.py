from __future__ import annotations

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Add src to path to import suite components
sys.path.append(str(Path(__file__).parent.parent / "src"))

from heidi_cli.shared.config import ConfigLoader

console = Console()

def check_structure():
    """Verify modular structure exists."""
    base = Path(__file__).parent.parent / "src" / "heidi_cli"
    modules = ["model_host", "runtime", "pipeline", "registry", "shared"]
    results = []
    for m in modules:
        path = base / m
        results.append((m, path.exists() and path.is_dir()))
    return results

def check_docs():
    """Verify documentation exists."""
    base = Path(__file__).parent.parent / "docs"
    docs = ["architecture.md", "model-host.md", "auto-registration.md"]
    results = []
    for d in docs:
        path = base / d
        results.append((d, path.exists()))
    return results

def check_config():
    """Verify config keys."""
    try:
        config = ConfigLoader.load()
        required_fields = ["suite_enabled", "data_root", "model_host_enabled", "models"]
        results = []
        for f in required_fields:
            results.append((f, hasattr(config, f)))
        return results
    except Exception as e:
        return [("config_load", False, str(e))]

def run_doctor():
    console.print(f"[bold]Learning Suite Doctor[/bold]\n")
    
    # Structure
    table = Table(title="Internal Structure")
    table.add_column("Module")
    table.add_column("Status")
    for mod, ok in check_structure():
        status = "[green]OK[/green]" if ok else "[red]MISSING[/red]"
        table.add_row(mod, status)
    console.print(table)
    
    # Docs
    table = Table(title="Documentation")
    table.add_column("File")
    table.add_column("Status")
    for doc, ok in check_docs():
        status = "[green]OK[/green]" if ok else "[red]MISSING[/red]"
        table.add_row(doc, status)
    console.print(table)
    
    # Config
    table = Table(title="Configuration")
    table.add_column("Key")
    table.add_column("Status")
    for key, ok in check_config():
        status = "[green]OK[/green]" if ok else "[red]MISSING[/red]"
        table.add_row(key, status)
    console.print(table)

if __name__ == "__main__":
    run_doctor()
