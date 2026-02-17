# SSH Connector

Secure SSH connector for Heidi CLI with local-only defaults and comprehensive audit logging.

## Overview

The SSH connector provides secure, audited SSH access through the Heidi backend. It is **disabled by default** and requires explicit configuration to enable.

## Security Model

### Non-Negotiable Defaults

- **OFF by default**: SSH connector is disabled unless explicitly enabled
- **Local-only bind**: Binds to 127.0.0.1 by default (no public exposure)
- **Target allowlist**: Only explicitly allowed targets can be accessed
- **No UI credential storage**: SSH keys/passwords never touch the browser
- **Audit everything**: All commands and connections are logged with redaction

### Feature Flag

```bash
# Enable SSH connector
export HEIDI_SSH_ENABLED=1

# Or set to empty/disabled
unset HEIDI_SSH_ENABLED
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEIDI_SSH_ENABLED` | (unset) | Set to `1` to enable SSH connector |
| `HEIDI_SSH_BIND` | `127.0.0.1` | Bind address (keep as localhost for security) |
| `HEIDI_SSH_TARGETS` | (empty) | Comma-separated allowlist of targets (e.g., `localhost:2222,192.168.1.100`) |
| `HEIDI_SSH_MAX_SESSIONS` | `5` | Maximum concurrent SSH sessions |
| `HEIDI_SSH_SESSION_TIMEOUT` | `300` | Session timeout in seconds (5 minutes) |
| `HEIDI_SSH_MAX_OUTPUT` | `10485760` | Max output size in bytes (10MB) |
| `HEIDI_SSH_BACKEND` | (not set) | SSH backend to use (currently ignored - exec is stub) |

> **Note**: Command execution (`/exec`) currently returns NOT_IMPLEMENTED. Set `HEIDI_SSH_BACKEND=asyncssh` for Phase 2 real SSH support.

### Target Allowlist Format

```bash
# Simple host (defaults to port 22)
export HEIDI_SSH_TARGETS="server.internal"

# Host with custom port
export HEIDI_SSH_TARGETS="localhost:2222"

# Multiple targets
export HEIDI_SSH_TARGETS="localhost:2222,192.168.1.100,server.internal"
```

## API Endpoints

> **⚠️ Implementation Status**: This documents the API design. Currently:
> - Session management: **IMPLEMENTED** (create, list, close)
> - Command execution (`/exec`): **STUB** - Returns NOT_IMPLEMENTED (requires `HEIDI_SSH_BACKEND=asyncssh`)
> - PTY streaming (`/pty/*`): **STUB** - Returns NOT_IMPLEMENTED (Phase 2)

All endpoints require authentication when `HEIDI_API_KEY` is set.

### Authentication

- **REST endpoints**: Use `X-Heidi-Key` header
- **Query parameter fallback**: Use `?key=<api_key>` for SSE/EventSource

### Endpoints

#### Create Session
```http
POST /api/connect/ssh/sessions
Content-Type: application/json
X-Heidi-Key: your-api-key

{
  "target": "localhost:2222",
  "user": "optional-override"
}
```

Response:
```json
{
  "session_id": "uuid-string",
  "target": "localhost:2222",
  "created_at": 1708195200.0
}
```

#### Execute Command (STUB)
> **Status**: Returns NOT_IMPLEMENTED. Requires `HEIDI_SSH_BACKEND=asyncssh` to be fully functional.

```http
POST /api/connect/ssh/sessions/{session_id}/exec
Content-Type: application/json
X-Heidi-Key: your-api-key

{
  "command": "ls -la",
  "cwd": "/home/user",
  "env": {"KEY": "value"}
}
```

Response (current stub):
```json
{
  "exit_code": -1,
  "stdout": "",
  "stderr": "SSH exec not implemented. Set HEIDI_SSH_BACKEND=asyncssh to enable.",
  "truncated": false
}
```

#### Close Session
```http
DELETE /api/connect/ssh/sessions/{session_id}
X-Heidi-Key: your-api-key
```

Response: `204 No Content`

#### List Sessions
```http
GET /api/connect/ssh/sessions
X-Heidi-Key: your-api-key
```

Response:
```json
[
  {
    "session_id": "uuid-string",
    "target": "localhost:2222",
    "user": "authenticated",
    "client_ip": "127.0.0.1",
    "created_at": 1708195200.0,
    "last_activity": 1708195500.0,
    "commands_executed": 5,
    "is_active": true
  }
]
```

#### Get Config
```http
GET /api/connect/ssh/config
X-Heidi-Key: your-api-key
```

Response:
```json
{
  "enabled": true,
  "bind_address": "127.0.0.1",
  "target_allowlist_count": 3,
  "validation_errors": []
}
```

## Audit Logging

All SSH operations are logged to an append-only audit log with automatic secret redaction.

### Log Location

```bash
# Default location
~/.local/share/heidi/ssh_audit.log

# Or via HEIDI_HOME
$HEIDI_HOME/ssh_audit.log
```

### Log Format

Each line is a JSON object:

```json
{"event": "session_created", "session_id": "...", "user": "...", "target": "...", "client_ip": "...", "timestamp": "2024-01-01T00:00:00Z", "ts": 1708195200.0}
{"event": "command_executed", "session_id": "...", "command": "ls -la", "exit_code": 0, "stdout_size": 1234, "stderr_size": 0, "duration_ms": 150.5, "timestamp": "...", "ts": ...}
{"event": "session_closed", "session_id": "...", "reason": "client_close", "commands_executed": 5, "timestamp": "...", "ts": ...}
```

### Secret Redaction

The following patterns are automatically redacted:

- Passwords: `password: "secret"` → `password: "[REDACTED]"`
- Tokens: `ghp_...` → `[REDACTED_GITHUB_TOKEN]`
- Private keys: `-----BEGIN RSA PRIVATE KEY-----...` → `[REDACTED]`

## Usage Examples

### Enable and Configure

```bash
# Enable SSH connector
export HEIDI_SSH_ENABLED=1

# Configure targets
export HEIDI_SSH_TARGETS="localhost:2222,dev-server.internal"

# Set API key for authentication
export HEIDI_API_KEY="your-secure-key"

# Start Heidi server
heidi serve
```

### Create Session and Execute Commands

```bash
# 1. Create a session
SESSION_RESPONSE=$(curl -s -X POST http://localhost:7777/api/connect/ssh/sessions \
  -H "Content-Type: application/json" \
  -H "X-Heidi-Key: your-secure-key" \
  -d '{"target": "localhost:2222"}')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')

# 2. Execute a command
curl -s -X POST "http://localhost:7777/api/connect/ssh/sessions/$SESSION_ID/exec" \
  -H "Content-Type: application/json" \
  -H "X-Heidi-Key: your-secure-key" \
  -d '{"command": "uptime"}'

# 3. Close the session
curl -s -X DELETE "http://localhost:7777/api/connect/ssh/sessions/$SESSION_ID" \
  -H "X-Heidi-Key: your-secure-key"
```

## Security Checklist

Before enabling SSH connector in production:

- [ ] SSH connector is disabled by default (`HEIDI_SSH_ENABLED` not set)
- [ ] Bind address is localhost (`HEIDI_SSH_BIND=127.0.0.1`)
- [ ] Target allowlist is explicitly configured (`HEIDI_SSH_TARGETS`)
- [ ] API key is set (`HEIDI_API_KEY`)
- [ ] Audit log directory is secured (0600 permissions)
- [ ] SSH keys are stored securely (not in browser/UI)
- [ ] Commands are restricted (command policy enforced)
- [ ] Session timeouts are appropriate
- [ ] Concurrent session limits are set

## Deployment Warnings

### Do NOT Expose SSH to Public Internet

The SSH connector is designed for local development and trusted networks only.

**DANGEROUS:**
```bash
# NEVER do this
export HEIDI_SSH_BIND="0.0.0.0"  # Exposes to all interfaces
export HEIDI_SSH_TARGETS="*"     # Allows any target
```

**SAFE:**
```bash
# Use a tunnel instead
ssh -L 7777:localhost:7777 user@remote-server
# Then access via localhost:7777
```

### Tunnel Recommendations

If you need remote access:

1. **SSH Tunnel** (recommended):
   ```bash
   ssh -L 7777:localhost:7777 user@server
   ```

2. **VPN**: Access through corporate VPN

3. **Cloudflare Tunnel**: With access policies (advanced)

## Troubleshooting

### SSH Endpoints Return 404

SSH connector is disabled. Enable it:
```bash
export HEIDI_SSH_ENABLED=1
```

### Target Blocked (403)

Add target to allowlist:
```bash
export HEIDI_SSH_TARGETS="your-host:port"
```

### Session Expired (404)

Sessions timeout after 5 minutes of inactivity. Create a new session.

### Authentication Failed (401)

Set API key:
```bash
export HEIDI_API_KEY="your-key"
```

#### PTY Session (Phase 2 - STUB)
> **Status**: NOT_IMPLEMENTED. Requires `HEIDI_SSH_BACKEND=asyncssh` to be fully functional.

##### Start PTY Session (STUB)
```http
POST /api/connect/ssh/sessions/{session_id}/pty
Content-Type: application/json
X-Heidi-Key: your-api-key

{
  "command": "/bin/bash",
  "cols": 80,
  "rows": 24
}
```

Response (current stub):
```json
{
  "pty_session_id": "pty-{session_id}",
  "message": "PTY streaming not yet implemented. Set HEIDI_SSH_BACKEND=asyncssh to enable in Phase 2."
}
```

##### PTY Stream (SSE - STUB)
```http
GET /api/connect/ssh/sessions/{session_id}/pty/{pty_session_id}/stream?key=your-api-key
```

Current stub response (text/event-stream):
```
data: PTY streaming not yet implemented. Set HEIDI_SSH_BACKEND=asyncssh to enable in Phase 2.
```

##### Resize PTY (STUB)
```http
POST /api/connect/ssh/sessions/{session_id}/pty/{pty_session_id}/resize?cols=80&rows=24
X-Heidi-Key: your-api-key
```

Response (current stub):
```json
{
  "message": "PTY resize not yet implemented. Set HEIDI_SSH_BACKEND=asyncssh to enable in Phase 2."
}
```

## Implementation Status

### Phase 1 (Current)
- ✅ Session management (create, list, close)
- ✅ Target allowlist enforcement
- ✅ Audit logging
- ✅ Security defaults (OFF by default, local-only bind, deny-by-default)

### Phase 2 (Requires `HEIDI_SSH_BACKEND=asyncssh`)
- [ ] Real SSH exec command execution
- [ ] PTY streaming via SSE (`/sessions/{id}/pty/stream`)
- [ ] Command policy enforcement (allowlist/denylist)
- [ ] Session persistence across server restarts
- [ ] Integration with SSH agent

### Future
- [ ] Multi-factor authentication
- [ ] paramiko backend alternative

## Related

- [Architecture Overview](../ARCHITECTURE.md)
- [Security Policy](../SECURITY.md)
- [CLI Commands](../CLI.md)
