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

import pytest
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


# ---- recall fixture (issue #3): realistic turn-endings that MUST fire ----
# Before this fixture existed, 9 of these 13 were missed: the sentence-start
# patterns anchored to ^ so any leading subject defeated them, "implemented" was
# missing from the standalone list, and there was no pattern for evidence-claims
# ("the tests pass", "CI is green") or subject-noun closures ("Task complete!").
# Each line here is a real claim shape an agent produces; if one stops firing,
# recall regressed silently and this is what makes it loud.
REALISTIC_DONE_CLAIMS = (
    "Task complete!",
    "I've implemented the retry logic in fetch_page.",
    "I finished the migration and pushed to main.",
    "the change is live",
    "The fix is in place.",
    "Implemented. Let me know if you want the tests too.",
    "I've added the retry logic and the three new tests pass.",
    "Your CI is green again.",
    "Everything is now wired up.",
    "The refactor is done.",
    "Fixed the off-by-one in the paginator.",
    "All set — the deploy went through.",
    "**DONE** — schema migration applied.",
)


def test_realistic_done_claims_fire(tmp_path):
    for text in REALISTIC_DONE_CLAIMS:
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out.get("decision") == "block", text


def test_first_person_lead_in_fires_only_with_determiner(tmp_path):
    # The optional "I've / we have / I just" prefix must not loosen the
    # determiner rule that keeps participle-adjective prose exempt.
    fires = ("I've fixed the tests.", "We have shipped the fix.", "I just resolved this ticket.")
    exempt = ("We have verified users in the table.", "I have finished reading the spec.",
              "It finished the migration overnight.")
    for text in fires:
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out.get("decision") == "block", text
    for text in exempt:
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text


def test_evidence_claims_need_a_check_noun(tmp_path):
    # "pass" / "green" are only claims when the subject is a check. Everyday
    # uses of the same words must not fire.
    for text in (
        "The light is green.",
        "The function is passing None to the callback.",
        "The button is wired to the handler.",
        "Live migration is supported.",
        "The tests should pass after that.",
        "The tests will pass once the fixture is updated.",
        "The tests don't pass yet.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text


def test_conditional_lead_in_does_not_fire(tmp_path):
    # Every line here MATCHES a claim pattern ("tests pass", "build is green",
    # "is complete") and is exempted ONLY by the non-assertive-clause guard.
    # Deleting _is_non_assertive_clause makes all of them block, so they
    # exercise the guard rather than pass by luck.
    for text in (
        "If the tests pass, we can ship on Friday.",
        "Once the build is green, cut the release.",
        "Unless the tests pass, don't merge.",
        "Make sure CI is green before merging.",
        "Run pytest to confirm the tests pass.",
        "Not all tests pass yet.",
        "I hope the migration is complete by Monday.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text


def test_conditional_guard_is_clause_scoped(tmp_path):
    # The guard inspects only the clause the match sits in. A lead-in in a
    # DIFFERENT clause does not launder a real claim. The dash cases matter
    # because an em/en dash divides clauses as firmly as a comma: without it in
    # CLAUSE_BOUNDARIES the "I hope" swallows a claim main already catches.
    for text in (
        "After adding the retry logic, the tests pass.",
        "The change is now live, if you want to test it.",
        "I hope this helps — the fix is complete.",
        "I hope this helps – the fix is complete.",
        "If you want, I can revert — the migration is done.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out.get("decision") == "block", text


def test_benign_prose_does_not_fire(tmp_path):
    # Sentences that share vocabulary with claims but assert nothing about the
    # work being finished.
    for text in (
        "I'm now working on the tests.",
        "Task completion is tracked in the ledger.",
        "Fix versions are listed in the changelog.",
        "Build artifacts go in dist/.",
        "Change done to the schema was minimal.",
        "Do the tests pass?",
        "Is the change live?",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text


def test_negated_and_attributed_claims_do_not_fire(tmp_path):
    # A clause that NEGATES or ATTRIBUTES a claim is not making it. Reported
    # from PR review: these all matched the evidence pattern before the guard
    # learned n't contractions and reporting verbs.
    for text in (
        "I don't think the build is green yet.",
        "I can't confirm the tests pass.",
        "The contributor says the tests pass.",
        "He said the migration is complete.",
        "According to the logs the tests pass.",
        "I cannot verify the tests pass.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text


def test_evidence_word_must_end_its_clause(tmp_path):
    # "passes" with a direct object is transitive prose, not a result claim.
    for text in (
        "The pipeline passes messages downstream.",
        "The check passes the token to the handler.",
        "The build passes environment variables through.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text


def test_quoted_claim_is_mentioned_not_made(tmp_path):
    # Quoting a claim as an EXAMPLE of a claim must not trip the gate. No
    # dedicated quote guard does this: the opening quote defeats the
    # sentence-start anchor, the closing quote fails the evidence pattern's
    # terminal lookahead, and EXEMPT_CONTEXT covers the quoted "is complete"
    # form. Pinned because that is three mechanisms holding one property up
    # by coincidence — if any of them moves, this is where it shows.
    quoted = (
        'The phrase "the tests pass" is the new pattern.',
        'I added "the migration is complete" to the fixture.',
        '"Task complete!" is what it printed.',
        'The string "Done." appears in the log.',
        '"Shipped the fix." is the example in the README.',
    )
    for text in quoted:
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text
    unquoted = 'He said "hello" to the user. The migration is complete.'
    out = _run({"transcript_path": _transcript(tmp_path, unquoted)},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out.get("decision") == "block", unquoted


def test_live_only_counts_when_it_ends_the_clause(tmp_path):
    # "live" is a closure verb only in "the change is live [now]". Attributive
    # and compound uses are ordinary English.
    for text in (
        "This is live data.",
        "This change is live-streaming to viewers.",
        "The dashboard is live-updating every second.",
        "This is live traffic from production.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out["continue"] is True, text
    for text in ("The change is live.", "The change is live now.", "the change is live"):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out.get("decision") == "block", text


def test_precision_fixes_did_not_cost_recall(tmp_path):
    # The tightening above must not eat ordinary result claims: "pass" followed
    # by an adverb or preposition is still a claim, so is a bare "is passing".
    for text in (
        "All tests pass on Python 3.12.",
        "The tests pass cleanly now.",
        "The build is passing.",
        "The tests pass and I pushed the branch.",
    ):
        out = _run({"transcript_path": _transcript(tmp_path, text)},
                   {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
        assert out.get("decision") == "block", text


@pytest.mark.xfail(strict=True, reason="known miss: 'confirmed' is too false-positive-prone to add blind")
def test_known_miss_confirmed_with_curl(tmp_path):
    # Documented gap, pinned so a fix is noticed (strict xfail turns green into
    # a failure, which is the prompt to delete this marker).
    out = _run({"transcript_path": _transcript(tmp_path,
                                                "The endpoint now returns 200 and I confirmed it with curl.")},
               {"CLAIM_CHECK_ENFORCE_MODE": "block", "CLAIM_CHECKS_LOG_PATH": _log_path(tmp_path)})
    assert out.get("decision") == "block"


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
