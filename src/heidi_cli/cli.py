from __future__ import annotations

import typer
import sys
from typing import Optional
import os
from pathlib import Path
from rich.console import Console

from .shared.config import ConfigLoader
from .launcher import start_daemon, stop_process, load_pids
from .token_tracking.cli import register_tokens_app

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
register_tokens_app(app)

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

@app.command()
def doctor():
    """Run suite verification checks."""
    from pathlib import Path
    
    # Locate the doctor script and run its main logic
    doctor_script = Path(__file__).parent.parent.parent / "scripts" / "doctor.py"
    if doctor_script.exists():
        # Read and execute the script in the current environment
        namespace = {"__file__": str(doctor_script)}
        # Ensure we don't accidentally recursively import cli
        exec(doctor_script.read_text(), namespace)
        if "run_doctor" in namespace:
            namespace["run_doctor"]()
        elif "check_all" in namespace:
            namespace["check_all"]()
    else:
        console.print(f"[red]Doctor script not found at {doctor_script}[/red]")

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

@memory_app.command("status")
def memory_status():
    """Show memory database status."""
    from .runtime.db import db
    conn = db.get_connection()
    counts = {
        "memories": conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0],
        "reflections": conn.execute("SELECT COUNT(*) FROM reflections").fetchone()[0],
        "rules": conn.execute("SELECT COUNT(*) FROM rules").fetchone()[0],
        "episodes": conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0],
    }
    console.print("[bold]Memory Database Status[/bold]")
    for table, count in counts.items():
        console.print(f" {table.capitalize()}: {count}")

@learning_app.command("reflect")
def learning_reflect(run_id: str, task: str, outcome: str):
    """Manually trigger reflection on a run."""
    import asyncio
    from .runtime.reflection import reflection_engine
    console.print(f"Reflecting on run {run_id}...")
    ref_id = asyncio.run(reflection_engine.reflect_on_run(run_id, task, outcome))
    console.print(f"[green]✓ Reflection created: {ref_id}[/green]")

@learning_app.command("export")
def learning_export(run_id: str):
    """(Phase 3 WIP) Export a run for manual review."""
    console.print(f"Exporting run {run_id} (Not implemented in Phase 3 skeleton)")

@learning_app.command("curate")
def learning_curate(date: Optional[str] = None):
    """Curate raw runs into redacted training datasets."""
    import asyncio
    from .pipeline.curation import curation_engine
    console.print(f"Curating dataset (Filter: {date or 'All'})...")
    count = asyncio.run(curation_engine.curate_dataset(date))
    console.print(f"[green]✓ Curated {count} runs into a new dataset.[/green]")

@learning_app.command("train-full")
def learning_train_full():
    """Start a background full-model retraining job."""
    import asyncio
    from .registry.retrain import retraining_engine
    console.print("Initiating background retraining...")
    try:
        job_id = asyncio.run(retraining_engine.start_retraining())
        console.print(f"[green]✓ Retraining job started: {job_id}[/green]")
    except Exception as e:
        console.print(f"[red]Error starting retraining: {e}[/red]")

@learning_app.command("eval")
def learning_eval(candidate_id: str):
    """Evaluate a candidate model against the active stable model."""
    import asyncio
    from .registry.eval import eval_harness
    console.print(f"Evaluating candidate {candidate_id}...")
    try:
        passed, results = asyncio.run(eval_harness.evaluate_candidate(candidate_id))
        status = "[green]PASSED[/green]" if passed else "[red]FAILED[/red]"
        console.print(f"Evaluation {status}. Metrics: {results['metrics']}")
    except Exception as e:
        console.print(f"[red]Error evaluating candidate: {e}[/red]")

@learning_app.command("promote")
def learning_promote(version_id: str, channel: str = "stable"):
    """Promote a model version to a specific channel (e.g. candidate or stable)."""
    import asyncio
    from .registry.manager import model_registry
    console.print(f"Promoting {version_id} to {channel}...")
    try:
        asyncio.run(model_registry.promote(version_id, channel))
        console.print(f"[green]✓ {version_id} promoted to {channel}.[/green]")
    except Exception as e:
        console.print(f"[red]Error promoting model: {e}[/red]")

@learning_app.command("rollback")
def learning_rollback():
    """Rollback to the previous stable model."""
    console.print("[yellow]Rollback mechanism not fully implemented in skeleton.[/yellow]")

@model_app.command("reload")
def model_reload():
    """Atomically hot-swap the model routing to the active stable model."""
    import asyncio
    from .registry.hotswap import hotswap_manager
    console.print("Initiating atomic hot-swap...")
    success = asyncio.run(hotswap_manager.reload_stable_model())
    if success:
        console.print("[green]✓ Hot-swap complete. Serving new state.[/green]")
    else:
        console.print("[red]Hot-swap failed. See logs.[/red]")

# Truth Path App - Dashboard integration commands
# These commands provide the single truth path for heidi-engine dashboard
truth_app = typer.Typer(help="Truth path commands for dashboard integration (get_status_field, stream_events)")
app.add_typer(truth_app, name="truth")


@truth_app.command("get_status_field")
def get_status_field_cmd(
    run_id: str = typer.Argument(..., help="Run ID to get status for"),
    timeout: int = typer.Option(5, "--timeout", "-t", help="Timeout in seconds"),
) -> None:
    """
    Get current status fields for a run.

    This command is the single truth path for heidi-engine dashboard.
    Returns JSON state for the specified run.

    Output format: JSON
    Timeout: 5 seconds default
    """
    import json
    import sys

    # Default status if backend not available
    default_status = {
        "run_id": run_id,
        "status": "unknown",
        "current_round": 0,
        "current_stage": "initializing",
        "stop_requested": False,
        "pause_requested": False,
        "counters": {
            "teacher_generated": 0,
            "teacher_failed": 0,
            "raw_written": 0,
            "validated_ok": 0,
            "rejected_schema": 0,
            "rejected_secret": 0,
            "rejected_dedupe": 0,
            "test_pass": 0,
            "test_fail": 0,
            "train_step": 0,
            "train_loss": 0.0,
            "eval_json_parse_rate": 0.0,
            "eval_format_rate": 0.0,
        },
        "usage": {
            "requests_sent": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "rate_limits_hit": 0,
            "retries": 0,
            "estimated_cost_usd": 0.0,
        },
    }

    # Try to get status from heidi-engine backend
    try:
        # Check if there's a heidi-engine state file we can read
        autotrain_dir = os.environ.get(
            "AUTOTRAIN_DIR",
            str(Path.home() / ".local" / "heidi-engine")
        )
        state_file = Path(autotrain_dir) / "runs" / run_id / "state.json"

        if state_file.exists():
            with open(state_file) as f:
                status_data = json.load(f)
                console.print(json.dumps(status_data))
                return
    except Exception:
        pass

    # Fallback to default status
    console.print(json.dumps(default_status))


@truth_app.command("stream_events")
def stream_events_cmd(
    run_id: str = typer.Argument(..., help="Run ID to stream events for"),
    timeout: int = typer.Option(5, "--timeout", "-t", help="Timeout in seconds"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum events to return"),
) -> None:
    """
    Stream events for a run.

    This command provides live event streaming for heidi-engine dashboard.
    Returns newline-separated JSON events.

    Output format: JSON lines (one JSON object per line)
    Timeout: 5 seconds default
    Disconnect: Returns immediately on timeout
    """
    import json
    import sys

    # Default empty events
    default_events = []

    # Try to get events from heidi-engine backend
    try:
        autotrain_dir = os.environ.get(
            "AUTOTRAIN_DIR",
            str(Path.home() / ".local" / "heidi-engine")
        )
        events_file = Path(autotrain_dir) / "runs" / run_id / "events.jsonl"

        if events_file.exists():
            events = []
            with open(events_file) as f:
                for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            events.append(event)
                            if len(events) >= limit:
                                break
                        except json.JSONDecodeError:
                            pass

            # Output as JSON lines
            for event in events:
                console.print(json.dumps(event))
            return
    except Exception:
        pass

    # Return empty if no events found
    # Note: We don't print anything for empty, caller handles no-output
    sys.exit(0)


if __name__ == "__main__":
    app()
    app()
