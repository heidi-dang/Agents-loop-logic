"""SSH Audit Logging

Append-only audit logging for SSH operations with secret redaction.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Secret patterns to redact in audit logs
SECRET_PATTERNS = [
    # Quoted values
    (r'(password["\']?\s*[:=]\s*)["\'][^"\']+["\']', r'\1"[REDACTED]"'),
    (r'(passwd["\']?\s*[:=]\s*)["\'][^"\']+["\']', r'\1"[REDACTED]"'),
    (r'(secret["\']?\s*[:=]\s*)["\'][^"\']+["\']', r'\1"[REDACTED]"'),
    (r'(token["\']?\s*[:=]\s*)["\'][^"\']+["\']', r'\1"[REDACTED]"'),
    (r'(key["\']?\s*[:=]\s*)["\']{20,}["\']', r'\1"[REDACTED]"'),
    # Unquoted values (e.g., password: secret123)
    (r'(password["\']?\s*[:=]\s*)([^\s"\']+)', r"\1[REDACTED]"),
    (r'(passwd["\']?\s*[:=]\s*)([^\s"\']+)', r"\1[REDACTED]"),
    (r'(secret["\']?\s*[:=]\s*)([^\s"\']+)', r"\1[REDACTED]"),
    (r'(token["\']?\s*[:=]\s*)([^\s"\']+)', r"\1[REDACTED]"),
    # Private keys
    (
        r"(-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----)[\s\S]+?(-----END \2 PRIVATE KEY-----)",
        r"\1\n[REDACTED]\n\3",
    ),
    # GitHub tokens
    (r"ghp_[a-zA-Z0-9]{30,40}", "[REDACTED_GITHUB_TOKEN]"),
    (r"github_pat_[a-zA-Z0-9]{20,30}_[a-zA-Z0-9]{50,60}", "[REDACTED_GITHUB_PAT]"),
]


def redact_secrets(text: str) -> str:
    """Redact secrets from text.

    Args:
        text: Input text that may contain secrets

    Returns:
        Text with secrets redacted
    """
    if not text:
        return text

    result = text
    for pattern, replacement in SECRET_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


class SSHAuditLogger:
    """Append-only audit logger for SSH operations."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        # Ensure log directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _append_entry(self, entry: Dict[str, Any]) -> None:
        """Append an entry to the audit log.

        Args:
            entry: Audit entry dictionary
        """
        # Add timestamp
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
        entry["ts"] = time.time()

        # Append to log file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    def log_session_created(
        self,
        session_id: str,
        user: str,
        target: str,
        client_ip: str,
    ) -> None:
        """Log session creation.

        Args:
            session_id: Session ID
            user: User who created the session
            target: Target host
            client_ip: Client IP address
        """
        self._append_entry(
            {
                "event": "session_created",
                "session_id": session_id,
                "user": user,
                "target": redact_secrets(target),
                "client_ip": client_ip,
            }
        )

    def log_command_executed(
        self,
        session_id: str,
        command: str,
        exit_code: int,
        stdout_size: int,
        stderr_size: int,
        duration_ms: float,
    ) -> None:
        """Log command execution.

        Args:
            session_id: Session ID
            command: Command that was executed
            exit_code: Exit code
            stdout_size: Size of stdout in bytes
            stderr_size: Size of stderr in bytes
            duration_ms: Execution duration in milliseconds
        """
        self._append_entry(
            {
                "event": "command_executed",
                "session_id": session_id,
                "command": redact_secrets(command),
                "exit_code": exit_code,
                "stdout_size": stdout_size,
                "stderr_size": stderr_size,
                "duration_ms": duration_ms,
            }
        )

    def log_session_closed(
        self,
        session_id: str,
        reason: str,
        commands_executed: int,
    ) -> None:
        """Log session closure.

        Args:
            session_id: Session ID
            reason: Reason for closure (timeout, client_close, error)
            commands_executed: Number of commands executed in session
        """
        self._append_entry(
            {
                "event": "session_closed",
                "session_id": session_id,
                "reason": reason,
                "commands_executed": commands_executed,
            }
        )

    def log_error(
        self,
        session_id: Optional[str],
        error_type: str,
        error_message: str,
    ) -> None:
        """Log an error.

        Args:
            session_id: Session ID (if applicable)
            error_type: Type of error
            error_message: Error message
        """
        self._append_entry(
            {
                "event": "error",
                "session_id": session_id,
                "error_type": error_type,
                "error_message": redact_secrets(error_message),
            }
        )

    def log_blocked_target(
        self,
        user: str,
        target: str,
        client_ip: str,
    ) -> None:
        """Log a blocked target attempt.

        Args:
            user: User who attempted
            target: Target that was blocked
            client_ip: Client IP address
        """
        self._append_entry(
            {
                "event": "blocked_target",
                "user": user,
                "target": redact_secrets(target),
                "client_ip": client_ip,
            }
        )


# Global audit logger instance
_audit_logger: Optional[SSHAuditLogger] = None


def get_audit_logger(log_path: Path) -> SSHAuditLogger:
    """Get or create the global audit logger instance.

    Args:
        log_path: Path to audit log file

    Returns:
        SSHAuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = SSHAuditLogger(log_path)
    return _audit_logger
