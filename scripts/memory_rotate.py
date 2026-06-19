#!/usr/bin/env python3
"""memory_rotate.py — keep your MEMORY.md index from becoming a wall.

A long index doesn't get read carefully (and some harnesses truncate). This checks the
index against a line/byte cap and tells you when it's time to consolidate — hand it to
the memory-steward agent, or trim by hand.

  python3 memory_rotate.py [path/to/MEMORY.md]     # default: ./memory/MEMORY.md

Caps (override via env):  MEMORY_LINE_CAP (default 200) · MEMORY_BYTE_CAP (default 25000)
Advisory only — always exits 0, never edits your file.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

LINE_CAP = int(os.environ.get("MEMORY_LINE_CAP", "200"))
BYTE_CAP = int(os.environ.get("MEMORY_BYTE_CAP", "25000"))


def main():
    path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path("memory/MEMORY.md")
    if not path.is_file():
        print(f"memory_rotate: no index at {path} (nothing to check)")
        sys.exit(0)

    data = path.read_text(errors="ignore")
    lines = len(data.splitlines())
    nbytes = len(data.encode())
    over = lines > LINE_CAP or nbytes > BYTE_CAP

    print(f"memory_rotate: {path}")
    print(f"  lines: {lines} / {LINE_CAP}")
    print(f"  bytes: {nbytes} / {BYTE_CAP}")
    print(f"  status: {'OVER CAP — time to consolidate' if over else 'ok'}")
    if over:
        print("  → run a consolidation pass: hand MEMORY.md to the memory-steward agent,")
        print("    or merge duplicates + prune dead pointers by hand. One scannable line per file.")
    sys.exit(0)


if __name__ == "__main__":
    main()
