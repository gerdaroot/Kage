"""Heartbeat file shared by the running bot and the Docker HEALTHCHECK.

Usage as a check: ``python -m kage._health [path]`` exits 0 when healthy.
Must stay free of heavy imports: it runs every healthcheck interval.
"""

import json
import os
import sys
import time
from pathlib import Path

HEARTBEAT_FILENAME = ".heartbeat"
MAX_HEARTBEAT_AGE = 120
DEFAULT_HEARTBEAT_PATH = Path("/data") / HEARTBEAT_FILENAME


def write_heartbeat(path: Path, connected: bool) -> None:
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(json.dumps({"ts": time.time(), "connected": connected}))
    os.replace(tmp_path, path)


def read_heartbeat(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def is_healthy(path: Path, max_age: float = MAX_HEARTBEAT_AGE) -> bool:
    beat = read_heartbeat(path)
    if not beat or not beat.get("connected"):
        return False
    try:
        return time.time() - float(beat["ts"]) <= max_age
    except (KeyError, TypeError, ValueError):
        return False


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_HEARTBEAT_PATH
    sys.exit(0 if is_healthy(target) else 1)
