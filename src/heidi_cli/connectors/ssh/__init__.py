"""SSH Connector Module

Secure SSH connector with local-only defaults and audit logging.
"""

from .config import is_ssh_enabled, is_target_allowed
from .session import SSHSession, get_session_manager
from .connector import create_session, close_session, exec_command
from .routes import router

__all__ = [
    "is_ssh_enabled",
    "is_target_allowed",
    "SSHSession",
    "get_session_manager",
    "create_session",
    "close_session",
    "exec_command",
    "router",
]
