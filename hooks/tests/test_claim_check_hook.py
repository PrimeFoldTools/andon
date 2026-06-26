#!/usr/bin/env python3
"""
Regression tests for claim_check_hook.py + log_claim.py.

The hook reads stdin JSON + env vars + a transcript file, so we exercise it as a
subprocess (the real production entry point) rather than importing it — that's the
only way the test reflects how the agent harness actually invokes it.

Run:  python3 -m pytest hooks/tests/ -q
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOOK = str(Path(__file__).resolve().parent.parent / "claim_check_hook.py")
WRITER = str(Path(__file__).resolve().parent.parent / "log_claim.py")


def _transcript(tmp_path, text):
    """A transcript with one CURRENT assistant entry (so the recency guard passes)."""
    p = tmp_path / "transcript.jsonl"
    entry = {
        "type": "assistant",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": {"content": [{"type": "text", "text": text}]},
    }
    p.write_text(json.dumps(entry) + "\n")
    return str(p)


def _clean_env(extra=None):
    env = dict(os.environ)
    env.pop("CLAIM_CHECK_ENFORCE_MODE", None)
    env.pop("CLAIM_CHECKS_LOG_PATH", None)
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
    return json.loads(r.stdout.strip().splitlines()[-1])


def _log_path(tmp_path):
    return str(tmp_path / "log.jsonl")


# ---- safe pass-through (must never crash / never spuriously block) ----
def test_off_mode_passes(tmp_path):
    out = _run({"transcript_path": _transcript(tmp_path, "all done and shipped")},
               {"CLAIM_CHECK_ENFORCE_MODE": "off"})
    assert out["continue"] is True and "decision" not in out


def test_empty_stdin_passes():
    r = subprocess.run([sys.executable, HOOK], input="", capture_output=True, text=True, env=_clean_env())
    assert r.returncode == 0
    assert json.loads(r.stdout.strip().splitlines()[-1])["continue"] is True


def test_malformed_stdin_passes():
    r = subprocess.run([sys.executable, HOOK], input="not json{", capture_output=True, text=True, env=_clean_env())
    assert r.returncode == 0
    assert json.loads(r.stdout.strip().splitlines()[-1])["continue"] is True


def test_stop_hook_active_passes(tmp_path):
    out = _run({"stop_hook_active": True, "transcript_path": _transcript(tmp_path, "this is done")})
    assert out["continue"] is True


def test_no_transcript_passes():
    assert _run({})["continue"] is True


def test_missing_transcript_file_passes(tmp_path):
    assert _run({"transcript_path": str(tmp_path / "nope.jsonl")})["continue"] is True


# ---- claim detection ----
def test_claim_without_log_warns_by_default(tmp_path):
    out = _run({"transcript_path": _transcript(tmp_path, "The migration is complete.")},
               {"CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out["continue"] is True and "systemMessage" in out  # warn, not block


def test_claim_without_log_blocks_in_block_mode(tmp_path):
    out = _run({"transcript_path": _transcript(tmp_path, "The migration is complete.")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out.get("decision") == "block" and "reason" in out


def test_common_done_claim_forms_block(tmp_path):
    # These are common agent closures; the original v1 detector only caught
    # auxiliary forms like "is complete" / "are fixed".
    for text in (
        "Done.",
        "Done — fixed.",
        "Shipped the fix.",
        "Fixed the tests.",
        "Implemented the migration.",
        "All set.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out.get("decision") == "block", text


def test_benign_participle_openers_do_not_fire(tmp_path):
    # Regression: the leading-action pattern must NOT fire on ordinary prose
    # that merely OPENS with a past-participle adjective ("Fixed income",
    # "Shipped goods"). It fires only on verb + determiner + object
    # ("Fixed the tests."). Without the determiner requirement these all
    # false-block — the exact thing a skeptic weaponizes against a hook repo.
    for text in (
        "Fixed income securities are stable this quarter.",
        "Shipped goods arrived at the dock this morning.",
        "Resolved disputes are common in arbitration.",
        "Completed applications go in the left tray.",
        "Verified users get a badge on their profile.",
        "Implemented designs need review before launch.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text


def test_no_claim_passes(tmp_path):
    out = _run({"transcript_path": _transcript(tmp_path, "Here is a summary of the options.")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out["continue"] is True


# ---- trimmed verbs: everyday English must NOT false-fire ----
def test_current_does_not_false_fire(tmp_path):
    out = _run({"transcript_path": _transcript(tmp_path, "The data is current as of yesterday.")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out["continue"] is True


def test_functional_does_not_false_fire(tmp_path):
    out = _run({"transcript_path": _transcript(tmp_path, "Is the new endpoint functional now?")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out["continue"] is True


def test_questions_do_not_false_fire(tmp_path):
    # The first three are question word-order that matches no pattern anyway.
    # The last three DO match a claim pattern and are exempted ONLY by the
    # question guard (verb+determiner / "are fixed" + a trailing "?") — deleting
    # the guard makes them block, so they actually exercise it (not pass-by-luck).
    for text in (
        "Are the tests fixed?",
        "Did we ship the fix?",
        "Is the migration complete?",
        "Shipped the fix?",
        "Fixed the tests already?",
        "The tests are fixed now?",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text


# ---- exemptions ----
def test_backtick_exempt(tmp_path):
    out = _run({"transcript_path": _transcript(tmp_path, "Set the flag `is done` in config.")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out["continue"] is True


def test_blockquote_exempt(tmp_path):
    out = _run({"transcript_path": _transcript(tmp_path, "> the feature is complete")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out["continue"] is True


# ---- the chicken-and-egg fix: log_claim.py creates the dir + satisfies the gate ----
def test_log_claim_creates_dir_and_appends(tmp_path):
    logp = tmp_path / "nested" / "deeper" / "log.jsonl"  # parent does NOT exist
    env = _clean_env({"CLAIM_CHECKS_LOG_PATH": str(logp)})
    r = subprocess.run([sys.executable, WRITER, "did X", "ran test Y"], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert logp.exists()
    entry = json.loads(logp.read_text().strip().splitlines()[-1])
    assert entry["claim"] == "did X" and entry["verification"] == "ran test Y"


def test_fresh_log_lets_claim_pass(tmp_path):
    logp = _log_path(tmp_path)
    env = _clean_env({"CLAIM_CHECKS_LOG_PATH": logp})
    subprocess.run([sys.executable, WRITER, "shipped feature", "ran pytest"],
                   capture_output=True, text=True, env=env, check=True)
    out = _run({"transcript_path": _transcript(tmp_path, "The feature is shipped.")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": logp})
    assert out["continue"] is True and "decision" not in out


def test_stale_log_does_not_satisfy_claim(tmp_path):
    # A verification entry OLDER than CLAIM_CHECK_FRESH_MIN (default 15min) must NOT
    # satisfy a fresh done-claim — otherwise "I verified something an hour ago" would
    # license any "done" now. Complements test_fresh_log_lets_claim_pass: together
    # they pin the freshness window from both sides.
    logp = tmp_path / "log.jsonl"
    stale_ts = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()
    logp.write_text(json.dumps({"timestamp": stale_ts, "claim": "x", "verification": "y"}) + "\n")
    out = _run({"transcript_path": _transcript(tmp_path, "The migration is complete.")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": str(logp)})
    assert out.get("decision") == "block"


def test_ignores_stale_prior_assistant_message(tmp_path):
    # Transcript-flush race guard: if the most-recent assistant entry is older than
    # STALE_THRESHOLD_S (30s) it belongs to a PRIOR turn — the hook must not block on
    # it even though it carries a done-claim and no fresh log exists.
    p = tmp_path / "transcript.jsonl"
    old_ts = (datetime.now(timezone.utc) - timedelta(seconds=300)).isoformat()
    entry = {"type": "assistant", "timestamp": old_ts,
             "message": {"content": [{"type": "text", "text": "The migration is complete."}]}}
    p.write_text(json.dumps(entry) + "\n")
    out = _run({"transcript_path": str(p)},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out["continue"] is True and "decision" not in out


def test_log_claim_requires_two_args(tmp_path):
    env = _clean_env({"CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    r = subprocess.run([sys.executable, WRITER, "only one"], capture_output=True, text=True, env=env)
    assert r.returncode == 2


def test_malformed_log_line_does_not_crash(tmp_path):
    # P0 regression: a non-string timestamp in the log must NOT crash the Stop hook —
    # the whole pitch is "fail-safe: any error passes the turn through." Pre-fix this
    # raised AttributeError and exited 1; the bad line must be skipped instead.
    logp = tmp_path / "log.jsonl"
    logp.write_text('{"ts": 12345}\n')  # int timestamp = malformed
    out = _run({"transcript_path": _transcript(tmp_path, "The migration is complete.")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": str(logp)})
    # Valid output (exit 0 is asserted in _run); bad line skipped → no fresh log → blocks.
    assert out.get("decision") == "block"
