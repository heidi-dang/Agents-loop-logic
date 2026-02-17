"""SSH Connector Core

SSH connection handling with stub implementation.
This module provides the API layer. Real SSH execution requires
a backend like asyncssh to be configured.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .config import is_target_allowed
from .session import SSHSession


class SSHConnectorError(Exception):
    """Base exception for SSH connector errors."""

    pass


class TargetNotAllowedError(SSHConnectorError):
    """Raised when target is not in allowlist."""

    pass


class NotImplementedError(SSHConnectorError):
    """Raised when SSH exec is called but no backend is configured."""

    pass


class SSHExecResult:
    """Result of an SSH command execution.

    Attributes:
        exit_code: Exit code from the command
        stdout: Standard output (truncated if too large)
        stderr: Standard error (truncated if too large)
        truncated: Whether output was truncated
    """

    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        truncated: bool = False,
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.truncated = truncated

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "truncated": self.truncated,
        }


def validate_target(target: str) -> Tuple[bool, str]:
    """Validate that a target is allowed.

    Args:
        target: Target host (with optional :port)

    Returns:
        Tuple of (is_allowed, error_message)
    """
    if not is_target_allowed(target):
        return (
            False,
            f"Target '{target}' is not in the allowlist. Add it via HEIDI_SSH_TARGETS env var.",
        )
    return True, ""


def exec_command(
    session: SSHSession,
    command: str,
    timeout: int = 60,
) -> SSHExecResult:
    """Execute a command on the target.

    This is a stub implementation. Real SSH execution requires
    a backend like asyncssh to be configured via HEIDI_SSH_BACKEND.

    Args:
        session: SSH session
        command: Command to execute
        timeout: Timeout in seconds (unused in stub)

    Returns:
        Execution result with NOT_IMPLEMENTED status

    Raises:
        TargetNotAllowedError: If target is not allowed
        NotImplementedError: If no SSH backend is configured
    """
    # Validate target
    is_allowed, error = validate_target(session.target)
    if not is_allowed:
        raise TargetNotAllowedError(error)

    # Stub: Return NOT_IMPLEMENTED
    # Real implementation would use asyncssh or paramiko
    return SSHExecResult(
        exit_code=-1,
        stdout="",
        stderr="SSH exec not implemented. Set HEIDI_SSH_BACKEND=asyncssh to enable.",
        truncated=False,
    )


def create_session(
    user: str,
    target: str,
    client_ip: str,
) -> Tuple[Optional[SSHSession], Optional[str]]:
    """Create an SSH session.

    Args:
        user: User creating the session
        target: Target host:port
        client_ip: Client IP address

    Returns:
        Tuple of (session, error_message)
    """
    from .session import get_session_manager

    # Validate target
    is_allowed, error = validate_target(target)
    if not is_allowed:
        return None, error

    # Create session
    session_manager = get_session_manager()
    session, error = session_manager.create_session(user, target, client_ip)

    return session, error


def close_session(session_id: str) -> Optional[SSHSession]:
    """Close an SSH session.

    Args:
        session_id: Session ID to close

    Returns:
        Closed session if found, None otherwise
    """
    from .session import get_session_manager

    session_manager = get_session_manager()
    return session_manager.close_session(session_id)


def get_session(session_id: str) -> Optional[SSHSession]:
    """Get a session by ID.

    Args:
        session_id: Session ID

    Returns:
        Session if found and active, None otherwise
    """
    from .session import get_session_manager

    session_manager = get_session_manager()
    return session_manager.get_session(session_id)
