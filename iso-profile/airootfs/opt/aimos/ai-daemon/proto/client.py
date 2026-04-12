"""
Unix socket client for AI_M_OS Go daemons.
Each daemon accepts a connection, writes one JSON payload, then closes.
"""
import socket
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SOCKET_PATHS = {
    "network": "/run/aimos/network-daemon.sock",
    "power":   "/run/aimos/power-daemon.sock",
    "sensor":  "/run/aimos/sensor-daemon.sock",
}

def read_daemon(name: str) -> dict | None:
    """Connect to daemon socket, read one JSON response, return dict or None."""
    path = SOCKET_PATHS.get(name)
    if not path or not Path(path).exists():
        logger.debug("Socket not available: %s", path)
        return None
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(path)
            data = b""
            while chunk := s.recv(4096):
                data += chunk
        return json.loads(data.decode())
    except Exception as e:
        logger.warning("Failed to read %s daemon: %s", name, e)
        return None
