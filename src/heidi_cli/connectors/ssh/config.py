"""SSH Connector Configuration

Feature flags and configuration for the SSH connector.
All settings are OFF by default for security.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Set

# Feature flag: SSH connector is OFF by default
# Set HEIDI_SSH_ENABLED=1 to enable
SSH_CONNECTOR_ENABLED = os.getenv("HEIDI_SSH_ENABLED", "").strip() == "1"

# Bind address: 127.0.0.1 by default (local-only)
# Only change this if you explicitly need external access (not recommended)
SSH_BIND_ADDRESS = os.getenv("HEIDI_SSH_BIND", "127.0.0.1").strip()

# Target allowlist: comma-separated list of allowed hosts
# Format: host:port or just host (defaults to 22)
# Example: HEIDI_SSH_TARGETS="localhost:2222,192.168.1.100,server.internal"
_ssh_targets_env = os.getenv("HEIDI_SSH_TARGETS", "").strip()
SSH_TARGET_ALLOWLIST: Set[str] = set()
if _ssh_targets_env:
    SSH_TARGET_ALLOWLIST = {t.strip() for t in _ssh_targets_env.split(",") if t.strip()}

# Max concurrent sessions (default: 5)
SSH_MAX_SESSIONS = int(os.getenv("HEIDI_SSH_MAX_SESSIONS", "5").strip() or "5")

# Session timeout in seconds (default: 300 = 5 minutes)
SSH_SESSION_TIMEOUT = int(os.getenv("HEIDI_SSH_SESSION_TIMEOUT", "300").strip() or "300")

# Max output size in bytes (default: 10MB)
SSH_MAX_OUTPUT_SIZE = int(os.getenv("HEIDI_SSH_MAX_OUTPUT", "10485760").strip() or "10485760")


# Audit log path (default: HEIDI_HOME/ssh_audit.log)
def get_ssh_audit_log_path() -> Path:
    """Get the SSH audit log path."""
    heidi_home = os.getenv("HEIDI_HOME")
    if heidi_home:
        return Path(heidi_home) / "ssh_audit.log"
    # Fallback to XDG_DATA_HOME or ~/.local/share/heidi
    xdg_data = os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg_data) / "heidi" / "ssh_audit.log"


SSH_AUDIT_LOG_PATH = get_ssh_audit_log_path()


def is_ssh_enabled() -> bool:
    """Check if SSH connector is enabled."""
    return SSH_CONNECTOR_ENABLED


def is_local_request(client_host: str) -> bool:
    """Check if request is from localhost."""
    return client_host in ("127.0.0.1", "localhost", "::1")


def is_target_allowed(target: str) -> bool:
    """Check if target is in allowlist.

    Args:
        target: Target string like "host:port" or "host"

    Returns:
        True if target is allowed, False otherwise
    """
    if not SSH_TARGET_ALLOWLIST:
        return False  # Deny by default if no allowlist

    # Normalize target
    if ":" not in target:
        target = f"{target}:22"

    # Check exact match
    if target in SSH_TARGET_ALLOWLIST:
        return True

    # Check host-only match (port 22 default)
    host = target.split(":")[0]
    if host in SSH_TARGET_ALLOWLIST:
        return True

    return False


def validate_config() -> List[str]:
    """Validate SSH connector configuration.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not SSH_CONNECTOR_ENABLED:
        return errors  # No validation needed if disabled

    if not SSH_TARGET_ALLOWLIST:
        errors.append("SSH connector enabled but no targets in allowlist (set HEIDI_SSH_TARGETS)")

    if SSH_BIND_ADDRESS not in ("127.0.0.1", "localhost", "::1"):
        errors.append(f"WARNING: SSH connector bound to {SSH_BIND_ADDRESS} (not localhost)")

    return errors
