"""
Thin Python wrapper around the compiled C `liveness` binary.
Falls back gracefully with a clear error if the binary hasn't been
built yet (see engine/liveness.c build instructions).
"""

from __future__ import annotations

import os
import subprocess

_BIN_PATH = os.path.join(os.path.dirname(__file__), "liveness")


def check_ports(host: str, ports: list[int], timeout: int = 15) -> dict[int, bool]:
    """Return {port: is_open} using the fast C engine.

    Raises FileNotFoundError if the binary hasn't been compiled yet
    (run: gcc -O2 -pthread -o liveness liveness.c inside sqlhawk/engine/).
    """
    if not os.path.exists(_BIN_PATH):
        raise FileNotFoundError(
            f"Liveness engine not built. Run:\n"
            f"  gcc -O2 -pthread -o {_BIN_PATH} {_BIN_PATH}.c"
        )

    args = [_BIN_PATH, host] + [str(p) for p in ports]
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)

    results: dict[int, bool] = {}
    for line in proc.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) == 2:
            port, status = parts
            results[int(port)] = status == "open"
    return results
