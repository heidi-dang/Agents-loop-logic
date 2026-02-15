from __future__ import annotations

from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .render_policy import policy_from_env


@contextmanager
def safe_tty(console: Console):
    try:
        yield
    finally:
        try:
            console.show_cursor(True)
        except Exception:
            pass
        try:
            console.file.write("\x1b[0m\n")
            console.file.flush()
        except Exception:
            pass
        try:
            console.print()
        except Exception:
            pass


class StreamingUI:
    def __init__(self, disable: bool = False):
        self.disable = disable
        self.console = Console()
        self.progress = None
        self.live = None
        self.current_task = ""
        self.task_id = None

    def start(self, task: str):
        if self.disable:
            self.console.print(f"[cyan]{task}...[/cyan]")
            return

        self.current_task = task
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )
        with safe_tty(self.console):
            self.progress.start()
            self.task_id = self.progress.add_task(task, total=None)

    def update(self, status: str):
        if self.disable:
            self.console.print(f"  {status}")
            return

        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, description=status)

    def stop(self, result: str = ""):
        if self.disable:
            if result:
                self.console.print(f"[green]{result}[/green]")
            return

        with safe_tty(self.console):
            try:
                if self.progress:
                    self.progress.stop()
            finally:
                self.progress = None
                self.task_id = None

            if result:
                self.console.print(Panel.fit(result, title="Done"))


def should_disable_live() -> bool:
    policy = policy_from_env()
    return not policy.allow_live
