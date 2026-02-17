"""SSH Connector FastAPI Routes

API endpoints for SSH connector with security defaults.
"""

from __future__ import annotations

import os
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from .config import (
    is_ssh_enabled,
    is_local_request,
    is_target_allowed,
    SSH_AUDIT_LOG_PATH,
    validate_config,
)
from .audit import get_audit_logger
from .connector import (
    create_session,
    close_session,
    get_session,
    exec_command,
    TargetNotAllowedError,
)

# Create router
router = APIRouter(prefix="/api/connect/ssh", tags=["ssh"])

# API key from environment (same as server.py)
HEIDI_API_KEY = os.getenv("HEIDI_API_KEY", "").strip()


def verify_auth(request: Request, key: Optional[str] = None) -> str:
    """Verify authentication.

    Args:
        request: FastAPI request
        key: Optional key from query string

    Returns:
        User identifier

    Raises:
        HTTPException: If authentication fails
    """
    # If no API key configured, allow all (for development)
    if not HEIDI_API_KEY:
        return "anonymous"

    # Check header first
    header_key = request.headers.get("x-heidi-key", "").strip()
    effective_key = header_key or key or ""

    if effective_key != HEIDI_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return "authenticated"


def check_ssh_enabled():
    """Check if SSH connector is enabled.

    Raises:
        HTTPException: If SSH connector is disabled
    """
    if not is_ssh_enabled():
        raise HTTPException(
            status_code=404, detail="SSH connector is disabled. Set HEIDI_SSH_ENABLED=1 to enable."
        )


# Request/Response models
class CreateSessionRequest(BaseModel):
    target: str
    user: Optional[str] = None
    port: Optional[int] = 22


class CreateSessionResponse(BaseModel):
    session_id: str
    target: str
    created_at: float


class ExecRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    env: Optional[dict] = None


class ExecResponse(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    truncated: bool


class SessionInfo(BaseModel):
    session_id: str
    target: str
    user: str
    client_ip: str
    created_at: float
    last_activity: float
    commands_executed: int
    is_active: bool


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_ssh_session(
    request: Request,
    body: CreateSessionRequest,
    key: Optional[str] = None,
    user: str = Depends(verify_auth),
):
    """Create an SSH session.

    Args:
        request: FastAPI request
        body: Session creation parameters
        key: Optional API key from query string
        user: Authenticated user

    Returns:
        Created session info
    """
    check_ssh_enabled()

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Check local-only policy (optional enforcement)
    # If HEIDI_SSH_BIND is not localhost, skip this check
    # For now, just log it
    if not is_local_request(client_ip):
        # In strict mode, you might want to reject non-local requests
        # For MVP, we allow but audit
        pass

    # Validate target
    target = body.target
    if body.port and body.port != 22:
        target = f"{body.target}:{body.port}"

    if not is_target_allowed(target):
        # Log blocked attempt
        audit = get_audit_logger(SSH_AUDIT_LOG_PATH)
        audit.log_blocked_target(user, target, client_ip)

        raise HTTPException(
            status_code=403,
            detail=f"Target '{target}' is not in the allowlist. Add it via HEIDI_SSH_TARGETS env var.",
        )

    # Create session
    session, error = create_session(
        user=user,
        target=target,
        client_ip=client_ip,
    )

    if error:
        raise HTTPException(status_code=500, detail=error)

    # Log creation
    audit = get_audit_logger(SSH_AUDIT_LOG_PATH)
    audit.log_session_created(session.id, user, target, client_ip)

    return CreateSessionResponse(
        session_id=session.id,
        target=target,
        created_at=session.created_at,
    )


@router.post("/sessions/{session_id}/exec", response_model=ExecResponse)
async def exec_ssh_command(
    session_id: str,
    body: ExecRequest,
    key: Optional[str] = None,
    user: str = Depends(verify_auth),
):
    """Execute a command in an SSH session.

    Args:
        session_id: Session ID
        body: Command execution parameters
        key: Optional API key from query string
        user: Authenticated user

    Returns:
        Command execution result
    """
    check_ssh_enabled()

    # Get session
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Execute command
    start_time = time.time()

    try:
        result = exec_command(session, body.command)
    except TargetNotAllowedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    duration_ms = (time.time() - start_time) * 1000

    # Record command
    session.record_command()

    # Log execution
    audit = get_audit_logger(SSH_AUDIT_LOG_PATH)
    audit.log_command_executed(
        session_id=session_id,
        command=body.command,
        exit_code=result.exit_code,
        stdout_size=len(result.stdout),
        stderr_size=len(result.stderr),
        duration_ms=duration_ms,
    )

    return ExecResponse(
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
        truncated=result.truncated,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def close_ssh_session(
    session_id: str,
    key: Optional[str] = None,
    user: str = Depends(verify_auth),
):
    """Close an SSH session.

    Args:
        session_id: Session ID to close
        key: Optional API key from query string
        user: Authenticated user
    """
    check_ssh_enabled()

    # Get session before closing
    session = get_session(session_id)
    commands_executed = session.commands_executed if session else 0

    # Close session
    closed = close_session(session_id)

    if not closed:
        raise HTTPException(status_code=404, detail="Session not found")

    # Log closure
    audit = get_audit_logger(SSH_AUDIT_LOG_PATH)
    audit.log_session_closed(
        session_id=session_id,
        reason="client_close",
        commands_executed=commands_executed,
    )

    return None


@router.get("/sessions", response_model=list[SessionInfo])
async def list_ssh_sessions(
    key: Optional[str] = None,
    user: str = Depends(verify_auth),
):
    """List active SSH sessions.

    Args:
        key: Optional API key from query string
        user: Authenticated user

    Returns:
        List of active sessions
    """
    check_ssh_enabled()

    from .session import get_session_manager

    session_manager = get_session_manager()
    sessions = session_manager.list_sessions(user=user if user != "anonymous" else None)

    return [
        SessionInfo(
            session_id=s.id,
            target=s.target,
            user=s.user,
            client_ip=s.client_ip,
            created_at=s.created_at,
            last_activity=s.last_activity,
            commands_executed=s.commands_executed,
            is_active=s.is_active,
        )
        for s in sessions
    ]


@router.get("/config")
async def get_ssh_config(
    key: Optional[str] = None,
    user: str = Depends(verify_auth),
):
    """Get SSH connector configuration (safe subset).

    Args:
        key: Optional API key from query string
        user: Authenticated user

    Returns:
        Configuration info
    """
    check_ssh_enabled()

    errors = validate_config()

    return {
        "enabled": is_ssh_enabled(),
        "bind_address": os.getenv("HEIDI_SSH_BIND", "127.0.0.1"),
        "target_allowlist_count": len(os.getenv("HEIDI_SSH_TARGETS", "").split(",")),
        "validation_errors": errors,
    }


# PTY Streaming endpoints (Phase 2 - stubbed for future implementation)
# These require a real SSH backend (asyncssh) to be fully functional


class PTYStartRequest(BaseModel):
    command: str
    cols: int = 80
    rows: int = 24


class PTYStartResponse(BaseModel):
    pty_session_id: str
    message: str


@router.post("/sessions/{session_id}/pty", response_model=PTYStartResponse)
async def start_pty_session(
    session_id: str,
    body: PTYStartRequest,
    key: Optional[str] = None,
    user: str = Depends(verify_auth),
):
    """Start a PTY session for interactive command execution.

    Phase 2: Requires HEIDI_SSH_BACKEND=asyncssh to be fully functional.
    Currently returns NOT_IMPLEMENTED stub.

    Args:
        session_id: SSH session ID
        body: PTY start parameters
        key: Optional API key from query string
        user: Authenticated user

    Returns:
        PTY session info
    """
    check_ssh_enabled()

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return PTYStartResponse(
        pty_session_id=f"pty-{session_id}",
        message="PTY streaming not yet implemented. Set HEIDI_SSH_BACKEND=asyncssh to enable in Phase 2.",
    )


@router.post("/sessions/{session_id}/pty/{pty_session_id}/resize")
async def resize_pty(
    session_id: str,
    pty_session_id: str,
    cols: int = 80,
    rows: int = 24,
    key: Optional[str] = None,
    user: str = Depends(verify_auth),
):
    """Resize PTY terminal.

    Phase 2: Requires HEIDI_SSH_BACKEND=asyncssh to be fully functional.
    Currently returns NOT_IMPLEMENTED stub.

    Args:
        session_id: SSH session ID
        pty_session_id: PTY session ID
        cols: Terminal columns
        rows: Terminal rows
        key: Optional API key from query string
        user: Authenticated user
    """
    check_ssh_enabled()

    return {
        "message": "PTY resize not yet implemented. Set HEIDI_SSH_BACKEND=asyncssh to enable in Phase 2."
    }


@router.get("/sessions/{session_id}/pty/{pty_session_id}/stream")
async def stream_pty(
    session_id: str,
    pty_session_id: str,
    key: Optional[str] = None,
    user: str = Depends(verify_auth),
):
    """Stream PTY output (SSE).

    Phase 2: Requires HEIDI_SSH_BACKEND=asyncssh to be fully functional.
    Currently returns NOT_IMPLEMENTED stub.

    Args:
        session_id: SSH session ID
        pty_session_id: PTY session ID
        key: Optional API key from query string
        user: Authenticated user
    """
    check_ssh_enabled()

    from fastapi.responses import StreamingResponse

    async def stub_stream():
        yield "data: PTY streaming not yet implemented. Set HEIDI_SSH_BACKEND=asyncssh to enable in Phase 2.\n\n"

    return StreamingResponse(stub_stream(), media_type="text/event-stream")
