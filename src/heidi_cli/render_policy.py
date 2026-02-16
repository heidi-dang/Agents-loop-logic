from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional

import typer


@dataclass(frozen=True)
class RenderPolicy:
    plain: bool
    no_color: bool
    debug: bool
    is_tty: bool
    is_ci: bool

    @property
    def allow_live(self) -> bool:
        return (not self.plain) and (not self.is_ci) and self.is_tty


_TRUE = {"1", "true", "yes", "on"}


def _env_truthy(key: str) -> bool:
    return os.environ.get(key, "").strip().lower() in _TRUE


def _is_wsl() -> bool:
    if os.path.exists("/proc/version"):
        try:
            with open("/proc/version", "r") as f:
                content = f.read().lower()
                return "microsoft" in content or "wsl" in content
        except Exception:
            pass
    return False


def policy_from_env() -> RenderPolicy:
    is_ci = _env_truthy("CI")
    plain = _env_truthy("HEIDI_PLAIN")
    no_color = _env_truthy("HEIDI_NO_COLOR") or ("NO_COLOR" in os.environ)
    debug = _env_truthy("HEIDI_DEBUG")

    try:
        is_tty = bool(sys.stdout.isatty())
    except Exception:
        is_tty = False

    term = os.environ.get("TERM", "")
    if term.lower() == "dumb":
        is_tty = False

    is_wsl = _is_wsl()
    if is_wsl:
        is_tty = False

    return RenderPolicy(plain=plain, no_color=no_color, debug=debug, is_tty=is_tty, is_ci=is_ci)


def policy_from_ctx(ctx: Optional[typer.Context]) -> RenderPolicy:
    base = policy_from_env()
    if ctx is None or ctx.obj is None:
        return base

    flags = ctx.obj
    plain = bool(getattr(flags, "plain", base.plain))
    no_color = bool(getattr(flags, "no_color", base.no_color))
    debug = bool(getattr(flags, "debug", base.debug))

    return RenderPolicy(
        plain=plain,
        no_color=no_color,
        debug=debug,
        is_tty=base.is_tty,
        is_ci=base.is_ci,
    )
