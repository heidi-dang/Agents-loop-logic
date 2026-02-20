import os
import json
import socket
import time
from typing import Any, Dict, Optional

# Constants
DEFAULT_SOCKET_PATH = os.path.join(os.getenv("HEIDI_HOME", "${HOME}"), "run", "heidid.sock")
MAX_RETRIES = 2
BACKOFF_FACTOR = 0.5  # seconds
TIMEOUT = 30  # seconds for socket operations

class RPCError(Exception):
    """Exception raised for RPC errors returned by the server."""
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(f"RPC Error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data

class RPCClient:
    """Simple JSON‑RPC 2.0 client over a Unix domain socket.

    The client frames each JSON message with a 4‑byte big‑endian length prefix
    (max 512 KB as per the architecture spec). It automatically retries on
    connection failures with exponential back‑off.
    """

    def __init__(self, socket_path: Optional[str] = None):
        self.socket_path = socket_path or DEFAULT_SOCKET_PATH
        self._id_counter = 0

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    def _send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw = json.dumps(payload).encode("utf-8")
        if len(raw) > 512 * 1024:
            raise ValueError("Payload exceeds 512KB limit")
        # Length‑prefix (big‑endian unsigned int)
        length_prefix = len(raw).to_bytes(4, byteorder="big")
        for attempt in range(MAX_RETRIES + 1):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(0.5)  # Connect timeout < 1s
                    client.connect(self.socket_path)
                    client.settimeout(TIMEOUT)  # Request timeout
                    client.sendall(length_prefix + raw)
                    # Read response length prefix
                    resp_len_bytes = client.recv(4)
                    if len(resp_len_bytes) < 4:
                        raise ConnectionError("Incomplete response length prefix")
                    resp_len = int.from_bytes(resp_len_bytes, "big")
                    resp_data = b""
                    while len(resp_data) < resp_len:
                        chunk = client.recv(resp_len - len(resp_data))
                        if not chunk:
                            raise ConnectionError("Socket closed before full response received")
                        resp_data += chunk
                    response = json.loads(resp_data.decode("utf-8"))
                    return response
            except (OSError, ConnectionError) as exc:
                if attempt < MAX_RETRIES:
                    backoff = BACKOFF_FACTOR * (2 ** attempt)
                    time.sleep(backoff)
                else:
                    raise ConnectionError(f"Failed to communicate with heidid after {MAX_RETRIES + 1} attempts") from exc

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._next_id(),
        }
        response = self._send(request)
        if "error" in response and response["error"] is not None:
            err = response["error"]
            raise RPCError(err.get("code", -1), err.get("message", "Unknown error"), err.get("data"))
        return response.get("result")

# Convenience wrapper for the provider.generate method
def generate(**kwargs: Any) -> Dict[str, Any]:
    """Call the `provider.generate` RPC method.

    Parameters are passed directly to the RPC server. The function returns the
    parsed JSON‑RPC result dictionary as defined in the contract.
    """
    client = RPCClient()
    return client.call("provider.generate", kwargs)
