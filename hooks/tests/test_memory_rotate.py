#!/usr/bin/env python3
"""Tests for scripts/memory_rotate.py — the advisory index-size checker."""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent.parent / "scripts" / "memory_rotate.py")


def _run(path, env_extra=None):
    env = dict(os.environ)
    env.pop("MEMORY_LINE_CAP", None)
    env.pop("MEMORY_BYTE_CAP", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, SCRIPT, str(path)], capture_output=True, text=True, env=env)


def test_under_cap_ok(tmp_path):
    f = tmp_path / "MEMORY.md"
    f.write_text("# MEMORY\n- one line\n")
    r = _run(f)
    assert r.returncode == 0 and "status: ok" in r.stdout


def test_over_line_cap_warns(tmp_path):
    f = tmp_path / "MEMORY.md"
    f.write_text("\n".join(f"- line {i}" for i in range(50)))
    r = _run(f, {"MEMORY_LINE_CAP": "10"})
    assert r.returncode == 0 and "OVER CAP" in r.stdout


def test_missing_file_ok(tmp_path):
    r = _run(tmp_path / "nope.md")
    assert r.returncode == 0 and "nothing to check" in r.stdout
