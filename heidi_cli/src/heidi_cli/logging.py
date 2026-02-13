from __future__ import annotations

import json
import logging
import re
import uuid
import contextvars
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.logging import RichHandler

from .config import ConfigManager


console = Console()

SECRET_PATTERNS = [
    (re.compile(r"(ghp_[a-zA-Z0-9]{36})"), "***REDACTED***"),
    (re.compile(r"(github_pat_[a-zA-Z0-9_]{22,})"), "***REDACTED***"),
    (re.compile(r"(COPILOT_GITHUB_TOKEN=)([^\s]*)"), r"\1***REDACTED***"),
    (re.compile(r"(GH_TOKEN=)([^\s]*)"), r"\1***REDACTED***"),
    (re.compile(r"(GITHUB_TOKEN=)([^\s]*)"), r"\1***REDACTED***"),
    (re.compile(r"\b(GH_TOKEN|GITHUB_TOKEN|COPILOT_GITHUB_TOKEN)\b\s*[:=]\s*([^\s\"']+)"), r"\1=***REDACTED***"),
    (re.compile(r"\b(COPILOT_[A-Z0-9_]+)\b\s*[:=]\s*([^\s\"']+)"), r"\1=***REDACTED***"),
    (re.compile(r"\b(OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY|OPEN_ROUTER_API_KEY)\b\s*[:=]\s*([^\s\"']+)"), r"\1=***REDACTED***"),
    (re.compile(r"\"(github_token|copilot_github_token|gh_token)\"\s*:\s*\"([^\"]+)\"", re.IGNORECASE), r"\"\1\":\"***REDACTED***\""),
]


def redact_secrets(text: str) -> str:
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class HeidiLogger:
    _run_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "heidi_run_id",
        default=None,
    )
    _run_dir_var: contextvars.ContextVar[Optional[Path]] = contextvars.ContextVar(
        "heidi_run_dir",
        default=None,
    )
    _logger_var: contextvars.ContextVar[Optional[logging.Logger]] = contextvars.ContextVar(
        "heidi_logger",
        default=None,
    )

    @classmethod
    def init_run(cls, run_id: Optional[str] = None) -> str:
        resolved = run_id or str(uuid.uuid4())[:8]
        run_dir = ConfigManager.RUNS_DIR / resolved
        run_dir.mkdir(parents=True, exist_ok=True)

        cls._run_id_var.set(resolved)
        cls._run_dir_var.set(run_dir)

        logger = logging.getLogger(f"heidi.{resolved}")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()

        file_handler = logging.FileHandler(run_dir / "stdout.log")
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(file_handler)
        cls._logger_var.set(logger)

        cls.write_run_meta(
            {
                "run_id": resolved,
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
            }
        )

        return resolved

    @classmethod
    def _redact_meta(cls, value: Any) -> Any:
        if isinstance(value, str):
            return redact_secrets(value)
        if isinstance(value, dict):
            return {k: cls._redact_meta(v) for k, v in value.items()}
        if isinstance(value, list):
            return [cls._redact_meta(v) for v in value]
        return value

    @classmethod
    def get_run_dir(cls) -> Optional[Path]:
        return cls._run_dir_var.get()

    @classmethod
    def get_run_id(cls) -> Optional[str]:
        return cls._run_id_var.get()

    @classmethod
    def debug(cls, msg: str) -> None:
        redacted = redact_secrets(msg)
        logger = cls._logger_var.get()
        if logger:
            logger.debug(redacted)
        console.print(f"[dim]{redacted}[/dim]")

    @classmethod
    def info(cls, msg: str) -> None:
        redacted = redact_secrets(msg)
        logger = cls._logger_var.get()
        if logger:
            logger.info(redacted)
        console.print(redacted)

    @classmethod
    def warning(cls, msg: str) -> None:
        redacted = redact_secrets(msg)
        logger = cls._logger_var.get()
        if logger:
            logger.warning(redacted)
        console.print(f"[yellow]WARNING: {redacted}[/yellow]")

    @classmethod
    def error(cls, msg: str) -> None:
        redacted = redact_secrets(msg)
        logger = cls._logger_var.get()
        if logger:
            logger.error(redacted)
        console.print(f"[red]ERROR: {redacted}[/red]")

    @classmethod
    def emit_status(cls, status: str) -> None:
        cls.info(f"[STATUS] {status}")

    @classmethod
    def emit_log(cls, source: str, message: str) -> None:
        cls.info(f"[{source}] {message}")

    @classmethod
    def emit_result(cls, result: str) -> None:
        cls.info(f"[RESULT] {result}")

    @classmethod
    def write_event(cls, event_type: str, data: dict[str, Any]) -> None:
        run_dir = cls._run_dir_var.get()
        if not run_dir:
            return
        redacted_data = {k: redact_secrets(str(v)) for k, v in data.items()}
        transcript_file = run_dir / "transcript.jsonl"
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "data": redacted_data,
        }
        with open(transcript_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    @classmethod
    def write_run_meta(cls, metadata: dict[str, Any]) -> None:
        run_dir = cls._run_dir_var.get()
        if not run_dir:
            return
        run_file = run_dir / "run.json"
        base: dict[str, Any] = {}
        if run_file.exists():
            try:
                base = json.loads(run_file.read_text())
            except Exception:
                base = {}

        updated = dict(base)
        updated.update(metadata)
        updated["updated_at"] = datetime.utcnow().isoformat()
        run_file.write_text(json.dumps(cls._redact_meta(updated), indent=2))


def setup_global_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )
