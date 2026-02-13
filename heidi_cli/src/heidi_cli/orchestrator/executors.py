from __future__ import annotations

import asyncio
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from ..copilot_runtime import CopilotRuntime
from ..logging import redact_secrets


@dataclass
class ExecResult:
    ok: bool
    output: str
    events: list[dict[str, Any]] = None

    def __post_init__(self):
        if self.events is None:
            self.events = []  # type: ignore[assignment]


class BaseExecutor:
    async def run(self, prompt: str, workdir: Path) -> ExecResult:
        raise NotImplementedError


class CopilotExecutor(BaseExecutor):
    def __init__(self, model: Optional[str] = None, cwd: Optional[Path] = None):
        self.model = model
        self.cwd = cwd

    async def run(self, prompt: str, workdir: Path) -> ExecResult:
        rt = CopilotRuntime(model=self.model, cwd=workdir or self.cwd)
        await rt.start()
        try:
            text = await rt.send_and_wait(f"WORKDIR: {workdir}\n\n{prompt}")
            return ExecResult(ok=True, output=text)
        except Exception as e:
            return ExecResult(ok=False, output=redact_secrets(str(e)))
        finally:
            await rt.stop()


class SubprocessExecutor(BaseExecutor):
    def __init__(self, cmd_prefix: list[str]):
        self.cmd_prefix = cmd_prefix

    async def run(self, prompt: str, workdir: Path) -> ExecResult:
        cmd = self.cmd_prefix + [prompt]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(workdir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        text = (out or b"").decode(errors="replace")
        return ExecResult(ok=(proc.returncode == 0), output=redact_secrets(text))


class OpenCodeExecutor(SubprocessExecutor):
    def __init__(self):
        override = (os.getenv("HEIDI_OPENCODE_CMD") or "").strip()
        super().__init__(
            shlex.split(override, posix=(os.name != "nt")) if override else ["opencode", "run"]
        )


class JulesExecutor(SubprocessExecutor):
    def __init__(self):
        override = (os.getenv("HEIDI_JULES_CMD") or "").strip()
        super().__init__(
            shlex.split(override, posix=(os.name != "nt"))
            if override
            else ["jules", "remote", "new", "--session"]
        )


class VscodeExecutor(BaseExecutor):
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port

    async def run(self, prompt: str, workdir: Path) -> ExecResult:
        try:
            proc = await asyncio.create_subprocess_exec(
                "code",
                "--folder-uri",
                workdir.resolve().as_uri(),
                "--command", "heidi-vscode.execute",
                "--",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            out, _ = await proc.communicate()
            text = (out or b"").decode(errors="replace")
            return ExecResult(ok=(proc.returncode == 0), output=redact_secrets(text))
        except FileNotFoundError:
            return ExecResult(ok=False, output=redact_secrets("VS Code not found in PATH"))
