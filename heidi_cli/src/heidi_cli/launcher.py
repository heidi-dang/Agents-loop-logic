from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from typing import Optional, Tuple

from rich.console import Console
from rich.progress import SpinnerColumn, TextColumn, Progress

console = Console()


def wait_for_server(host: str, port: int, timeout: int = 15) -> bool:
    """Wait for server to be ready by polling /health endpoint."""
    start_time = time.time()
    url = f"http://{host}:{port}/health"
    
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except (urllib.error.URLError, socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
    
    return False


def start_server_subprocess(
    host: str = "127.0.0.1",
    port: int = 7777,
) -> subprocess.Popen:
    """Start the Heidi server as a subprocess."""
    env = os.environ.copy()
    env["HEIDI_NO_WIZARD"] = "1"
    
    cmd = [
        sys.executable, "-m", "heidi_cli", "serve",
        "--host", host,
        "--port", str(port),
    ]
    
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    
    return process


def check_port_available(host: str, port: int) -> bool:
    """Check if a port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False


def find_available_port(host: str, start_port: int = 7777) -> int:
    """Find an available port starting from start_port."""
    port = start_port
    while port < start_port + 100:
        if check_port_available(host, port):
            return port
        port += 1
    raise RuntimeError(f"Could not find available port near {start_port}")


def start_server(
    host: str = "127.0.0.1",
    port: int = 7777,
    wait: bool = True,
    timeout: int = 15,
) -> Tuple[subprocess.Popen, int]:
    """
    Start the Heidi server and optionally wait for it to be ready.
    
    Returns (process, actual_port) tuple.
    """
    actual_port = port
    if not check_port_available(host, port):
        console.print(f"[yellow]Port {port} not available, finding available port...[/yellow]")
        actual_port = find_available_port(host, port)
    
    console.print(f"[cyan]Starting Heidi server on {host}:{actual_port}...[/cyan]")
    
    process = start_server_subprocess(host, actual_port)
    
    if wait:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Waiting for server to be ready...", total=None)
            if wait_for_server(host, actual_port, timeout):
                progress.update(task, completed=True)
                console.print(f"[green]Server ready at http://{host}:{actual_port}[/green]")
            else:
                console.print(f"[red]Server failed to start within {timeout}s[/red]")
                process.terminate()
                raise RuntimeError("Server failed to start")
    
    return process, actual_port


def stop_server(process: Optional[subprocess.Popen]) -> None:
    """Stop the server process gracefully."""
    if process is None:
        return
    
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    except Exception as e:
        console.print(f"[yellow]Warning: Error stopping server: {e}[/yellow]")


def is_server_running(host: str, port: int) -> bool:
    """Check if server is running."""
    try:
        urllib.request.urlopen(f"http://{host}:{port}/health", timeout=2)
        return True
    except Exception:
        return False
