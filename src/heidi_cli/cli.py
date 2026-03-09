from __future__ import annotations

import typer
import sys
from rich.console import Console

from .shared.config import ConfigLoader
from .launcher import start_daemon, stop_process, load_pids

console = Console()
app = typer.Typer(
    add_completion=False,
    help="Heidi Unified Learning Suite CLI",
)

# New Module Sub-apps
model_app = typer.Typer(help="Local model management (serve/status/stop/reload)")
memory_app = typer.Typer(help="Memory management (status/search)")
learning_app = typer.Typer(help="Learning & Training management (reflect/export/curate/train-full/eval/promote/rollback)")

app.add_typer(model_app, name="model")
app.add_typer(memory_app, name="memory")
app.add_typer(learning_app, name="learning")

@app.command()
def status():
    """Show suite status."""
    config = ConfigLoader.load()
    console.print("[bold]Learning Suite Status[/bold]")
    console.print(f"Suite Enabled: {config.suite_enabled}")
    console.print(f"Data Root: {config.data_root}")
    console.print(f"Model Host: {config.host}:{config.port} (Enabled: {config.model_host_enabled})")
    
    pids = load_pids()
    if "model_host" in pids:
        console.print(f"Model Host PID: [green]{pids['model_host']}[/green]")
    else:
        console.print("Model Host PID: [red]Not running[/red]")

@model_app.command("serve")
def model_serve():
    """Start local model host daemon."""
    config = ConfigLoader.load()
    if not config.model_host_enabled:
        console.print("[red]Model host is disabled in config.[/red]")
        raise typer.Exit(1)
    
    pids = load_pids()
    if "model_host" in pids:
        console.print(f"[yellow]Model host already running (PID: {pids['model_host']})[/yellow]")
        return

    console.print(f"Starting model host on {config.host}:{config.port}...")
    
    # Command to run uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn", "heidi_cli.model_host.server:app",
        "--host", config.host,
        "--port", str(config.port)
    ]
    
    pid = start_daemon("model_host", cmd, "model_host.log")
    console.print(f"[green]✓ Model host started (PID: {pid})[/green]")
    console.print(f"Logs: {config.data_root / 'logs' / 'model_host.log'}")

@model_app.command("status")
def model_status():
    """Check local model host status."""
    pids = load_pids()
    if "model_host" in pids:
        console.print(f"[green]Model host is running (PID: {pids['model_host']})[/green]")
    else:
        console.print("[red]Model host is not running.[/red]")

@model_app.command("stop")
def model_stop():
    """Stop local model host daemon."""
    if stop_process("model_host"):
        console.print("[green]✓ Model host stopped.[/green]")
    else:
        console.print("[yellow]Model host was not running.[/yellow]")

if __name__ == "__main__":
    app()
