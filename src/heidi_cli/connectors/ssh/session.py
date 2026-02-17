"""SSH Session Management

In-memory session store for SSH connections.
All sessions are ephemeral and time-bounded.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .config import SSH_MAX_SESSIONS, SSH_SESSION_TIMEOUT


@dataclass
class SSHSession:
    """Represents an SSH session.

    Attributes:
        id: Unique session ID
        user: User who created the session
        target: Target host:port
        client_ip: Client IP address
        created_at: Timestamp when session was created
        last_activity: Timestamp of last activity
        commands_executed: Number of commands executed
        is_active: Whether session is still active
    """

    id: str
    user: str
    target: str
    client_ip: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    commands_executed: int = 0
    is_active: bool = True

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        """Check if session has expired due to inactivity.

        Returns:
            True if session has timed out, False otherwise
        """
        return (time.time() - self.last_activity) > SSH_SESSION_TIMEOUT

    def record_command(self) -> None:
        """Record a command execution."""
        self.commands_executed += 1
        self.touch()


class SSHSessionManager:
    """Manages SSH sessions in memory.

    This is intentionally simple for MVP. In production,
    consider using Redis or similar for session storage.
    """

    def __init__(self):
        self._sessions: Dict[str, SSHSession] = {}

    def create_session(
        self,
        user: str,
        target: str,
        client_ip: str,
    ) -> Tuple[SSHSession, Optional[str]]:
        """Create a new SSH session.

        Args:
            user: User creating the session
            target: Target host:port
            client_ip: Client IP address

        Returns:
            Tuple of (session, error_message)
            If error_message is not None, session creation failed
        """
        # Check session limit
        self._cleanup_expired()

        if len(self._sessions) >= SSH_MAX_SESSIONS:
            return None, f"Maximum number of concurrent sessions reached ({SSH_MAX_SESSIONS})"

        # Create session
        session = SSHSession(
            id=str(uuid.uuid4()),
            user=user,
            target=target,
            client_ip=client_ip,
        )

        self._sessions[session.id] = session
        return session, None

    def get_session(self, session_id: str) -> Optional[SSHSession]:
        """Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session if found and not expired, None otherwise
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None

        if session.is_expired():
            session.is_active = False
            return None

        return session

    def close_session(self, session_id: str) -> Optional[SSHSession]:
        """Close a session.

        Args:
            session_id: Session ID to close

        Returns:
            Closed session if found, None otherwise
        """
        session = self._sessions.get(session_id)
        if session:
            session.is_active = False
            # Don't remove immediately - keep for audit purposes
        return session

    def list_sessions(self, user: Optional[str] = None) -> List[SSHSession]:
        """List active sessions.

        Args:
            user: Filter by user (optional)

        Returns:
            List of active (non-expired) sessions
        """
        self._cleanup_expired()

        sessions = [s for s in self._sessions.values() if s.is_active]
        if user:
            sessions = [s for s in sessions if s.user == user]
        return sessions

    def _cleanup_expired(self) -> None:
        """Remove expired sessions from memory."""
        expired_ids = [
            sid for sid, s in self._sessions.items() if s.is_expired() or not s.is_active
        ]
        for sid in expired_ids:
            del self._sessions[sid]

    def get_stats(self) -> Dict[str, int]:
        """Get session statistics.

        Returns:
            Dictionary with session counts
        """
        self._cleanup_expired()
        return {
            "active": len([s for s in self._sessions.values() if s.is_active]),
            "total": len(self._sessions),
            "max": SSH_MAX_SESSIONS,
        }


# Global session manager instance
_session_manager: Optional[SSHSessionManager] = None


def get_session_manager() -> SSHSessionManager:
    """Get or create the global session manager.

    Returns:
        SSHSessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SSHSessionManager()
    return _session_manager
