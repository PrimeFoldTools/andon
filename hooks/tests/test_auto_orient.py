#!/usr/bin/env python3
"""Regression tests for auto_orient.py (the UserPromptSubmit context-loader hook).

Run as a subprocess — the real production entry point (reads stdin JSON, emits the
UserPromptSubmit context-injection envelope).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = str(Path(__file__).resolve().parent.parent / "auto_orient.py")


def _clean_env(extra=None):
    env = dict(os.environ)
    for k in ("AUTO_ORIENT", "AUTO_ORIENT_MEMORY_PATH", "AUTO_ORIENT_MAX_BYTES"):
        env.pop(k, None)
    if extra:
        env.update(extra)
    return env


def _run(stdin_obj, env_extra=None):
    r = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(stdin_obj),
        capture_output=True, text=True, env=_clean_env(env_extra),
    )
    assert r.returncode == 0, r.stderr
    out = r.stdout.strip()
    return json.loads(out) if out else None


def _ctx(out):
    return out["hookSpecificOutput"]["additionalContext"]


def _mk_memory(tmp_path, text="# MEMORY\n- a durable fact\n"):
    d = tmp_path / "memory"
    d.mkdir(parents=True, exist_ok=True)
    (d / "MEMORY.md").write_text(text)
    return tmp_path


def test_injects_memory_on_first_prompt(tmp_path):
    proj = _mk_memory(tmp_path)
    out = _run({"cwd": str(proj), "session_id": f"first-{tmp_path.name}"})
    assert out is not None and "a durable fact" in _ctx(out)
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"


def test_once_per_session(tmp_path):
    proj = _mk_memory(tmp_path)
    sid = f"once-{tmp_path.name}"
    assert _run({"cwd": str(proj), "session_id": sid}) is not None      # first fires
    assert _run({"cwd": str(proj), "session_id": sid}) is None          # second is a no-op


def test_off_switch(tmp_path):
    proj = _mk_memory(tmp_path)
    assert _run({"cwd": str(proj), "session_id": f"off-{tmp_path.name}"}, {"AUTO_ORIENT": "off"}) is None


def test_no_memory_file_noop(tmp_path):
    assert _run({"cwd": str(tmp_path), "session_id": f"none-{tmp_path.name}"}) is None


def test_malformed_stdin_noop():
    r = subprocess.run([sys.executable, HOOK], input="not json{", capture_output=True, text=True, env=_clean_env())
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_empty_stdin_noop(tmp_path):
    # Run from a clean cwd: empty stdin → no cwd in JSON → hook falls back to os.getcwd();
    # with no memory/ there, it must no-op. (Determinism: don't depend on the test-runner's cwd.)
    r = subprocess.run([sys.executable, HOOK], input="", capture_output=True, text=True,
                       env=_clean_env(), cwd=str(tmp_path))
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_memory_path_override(tmp_path):
    f = tmp_path / "custom_MEMORY.md"
    f.write_text("# custom\n- override fact\n")
    out = _run({"cwd": str(tmp_path), "session_id": f"ov-{tmp_path.name}"},
               {"AUTO_ORIENT_MEMORY_PATH": str(f)})
    assert out is not None and "override fact" in _ctx(out)


def test_caps_at_max_bytes(tmp_path):
    proj = _mk_memory(tmp_path, "# MEMORY\n" + ("x" * 5000))
    out = _run({"cwd": str(proj), "session_id": f"cap-{tmp_path.name}"}, {"AUTO_ORIENT_MAX_BYTES": "500"})
    assert out is not None and "truncated" in _ctx(out)
