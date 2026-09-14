#!/usr/bin/env python3
"""
claim_check_hook.py — Stop-hook enforcer skeleton.

Blocks turn-end if the assistant claims "done / shipped / verified / complete"
without a recent verification log entry. Make the agent's done-claim mean
something.

USAGE
  1. Copy hooks/claim_check_hook.py + hooks/log_claim.py into your agent config dir
     (e.g. ~/.claude/hooks/).
  2. Register as a Stop hook in settings.json — MERGE into any existing "Stop" array,
     don't overwrite it:
       { "hooks": { "Stop": [{ "matcher": "*",
           "hooks": [{ "type": "command",
             "command": "CLAIM_CHECK_ENFORCE_MODE=warn python3 /abs/path/to/claim_check_hook.py" }] }] } }
  3. Tell your agent (in CLAUDE.md) that after it verifies a done-claim it must log it:
       python3 /abs/path/to/log_claim.py "what I claimed" "how I verified it"
     log_claim.py creates ~/.claude/state/claim_checks/log.jsonl on first run.
  4. Test it fired:
       echo '{"transcript_path":"/dev/null"}' | python3 claim_check_hook.py
       → should print {"continue": true, ...}
  5. Modes (default = warn; promote to block once you trust it):
       CLAIM_CHECK_ENFORCE_MODE=warn    # surface a warning, don't block  (DEFAULT)
       CLAIM_CHECK_ENFORCE_MODE=block   # block turn-end until a fresh log entry exists
       CLAIM_CHECK_ENFORCE_MODE=off     # silent pass-through

NOTE — this is a STOP hook; Stop hooks block with {"decision": "block"}.
A PreToolUse hook uses a DIFFERENT schema ({"hookSpecificOutput": {"permissionDecision": "deny"}}).
The two are NOT interchangeable — using the wrong one is a silent no-op.

CUSTOMIZE
  - COMPLETION_VERBS — closure verbs that trigger the check (kept tight to avoid false-fires).
  - OPT_IN_VERBS — looser verbs; enable only if your domain needs them.
  - EVIDENCE_NOUNS — the things whose "pass / green" is itself a done-claim (tests, CI, build).
  - CLOSURE_NOUNS — subjects for the bare "Task complete!" / "Migration done." form.
  - CLAIM_CHECK_FRESH_MIN — "fresh" window (15 is forgiving; don't go below ~5).
  - CLAIM_CHECKS_LOG_PATH env var — override the log location.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------- CONFIG (edit these) ----------
CLAIM_CHECKS_LOG = Path(
    os.environ.get(
        "CLAIM_CHECKS_LOG_PATH",
        str(Path.home() / ".claude" / "state" / "claim_checks" / "log.jsonl"),
    )
).expanduser()
CLAIM_CHECK_FRESH_MIN = 15      # minutes — log entries newer than this count as fresh
STALE_THRESHOLD_S = 30          # transcript-flush race guard
DEFAULT_MODE = "warn"           # warn | block | off  (start warn; promote to block once tuned)

# Unambiguous closure verbs — kept tight so everyday prose ("the data is current",
# "are we done here?") does NOT false-fire.
COMPLETION_VERBS = (
    "ready", "shipped", "complete", "completed", "done", "finished",
    "verified", "fixed", "resolved", "production[\\s-]ready",
    # State-of-the-thing closures: "the fix is in place", "everything is now
    # wired up". Bare "wired" is NOT included — "the button is wired to the
    # handler" is description, not closure. "live" is below, it needs a guard.
    "in[\\s-]place", "wired[\\s-]up",
)
# "live" is a closure only when it ENDS the clause: "the change is live",
# "the change is live now". Attributive and compound uses are ordinary English
# — "this is live data", "is live-streaming to viewers" — so it carries its own
# terminal guard instead of sitting in the list above.
LIVE_VERB = (
    r"live(?![-\u2010-\u2015\w])"
    r"(?=\s*(?:[.,;:!?)\]]|$|\b(?:now|again|already|and|on|in|for)\b))"
)
# Looser verbs — higher false-positive rate in normal English. Add deliberately if your
# domain needs them: "functional", "applied", "patched", "synced", "current",
# "in[\\s-]sync". NOT "working" — "I'm now working on the tests" would fire.
OPT_IN_VERBS = ()
COMPLETION_VERBS = COMPLETION_VERBS + OPT_IN_VERBS

# Evidence-claims: asserting a RESULT ("the tests pass", "CI is green") is the
# claim most in need of a verification record behind it — it is the one that
# sounds like evidence. Kept to nouns that name a check, so "the light is green"
# and "the function is passing None" do not fire.
EVIDENCE_NOUNS = (
    "tests?", "specs?", "ci", "builds?", "pipelines?", "checks?", "suite",
    "lints?", "linters?", "typechecks?",
)
# Subject-noun closures: "Task complete!", "Migration done." — a small noun list
# plus a closure verb, anchored to sentence start, so it stays narrow.
CLOSURE_NOUNS = (
    "task", "work", "job", "migration", "change", "fix", "deploy", "deployment",
    "refactor", "build", "patch", "update", "release", "rollout", "feature",
    "implementation", "cleanup", "ticket", "pr", "merge",
)


# ---------- PATTERNS ----------
_VERBS = "|".join(COMPLETION_VERBS + (LIVE_VERB,))
_EVIDENCE = "|".join(EVIDENCE_NOUNS)
_CLOSURE_NOUNS = "|".join(CLOSURE_NOUNS)
# Optional first-person lead-in for the sentence-start forms. Agents write
# "I've implemented the migration." far more often than "Implemented the
# migration." — without this the leading subject defeated both anchors.
_SUBJECT = r"(?:(?:i|we)(?:'ve|\s+have|\s+just|\s+have\s+just)?\s+)?"

CLAIM_PATTERNS = (
    # Standalone / sentence-start closure markers:
    # "Done.", "All set.", "Shipped:", "Ready — ..."
    re.compile(
        rf"(?im)(?:^|(?<=[.!?])\s+|\n)\s*"
        rf"(?:done|complete|completed|ready|verified|fixed|resolved|shipped|"
        rf"implemented|finished|production[\s-]ready|all\s+set)\b"
        rf"(?:\s*(?:[.!:;]|—|-)|\s*$)"
    ),
    # Subject-noun closure: "Task complete!", "Migration done." — bare noun +
    # closure verb with no copula. ("The fix is done." is the auxiliary
    # pattern below, not this one.)
    re.compile(
        rf"(?im)(?:^|(?<=[.!?])\s+|\n)\s*"
        rf"(?:(?:the|this|that)\s+)?(?:{_CLOSURE_NOUNS})\s+"
        rf"(?:done|complete|completed|finished|shipped|deployed|merged|applied|verified)\b"
        rf"(?:\s*(?:[.!:;]|—|-)|\s*$)"
    ),
    # Leading action-claim forms — REQUIRE a determiner after the verb so that
    # ordinary participle-adjective prose ("Fixed income securities…",
    # "Shipped goods arrived…", "Verified users get a badge…") does NOT
    # false-fire. Only "Shipped the fix.", "Fixed the tests.",
    # "Implemented the migration." (verb + determiner + object) trigger — with or
    # without a first-person lead-in ("I've implemented the migration.",
    # "We have fixed the tests.", "I finished the migration."). The determiner
    # requirement is what keeps "We have verified users in the table" exempt.
    re.compile(
        rf"(?im)(?:^|(?<=[.!?])\s+|\n)\s*{_SUBJECT}"
        rf"(?:shipped|fixed|verified|resolved|completed|implemented|finished)\s+"
        rf"(?:the|this|that|these|those|all|our|your|its|my)\b[^\n.!?]{{0,80}}"
    ),
    # "X is/are [already/now/fully] $VERB"
    re.compile(
        rf"\b(?:is|are|has\s+been|have\s+been|now|finally|fully|officially|already)"
        rf"(?:\s+(?:already|just|now|fully))?"
        rf"\s+(?:{_VERBS})\b",
        re.IGNORECASE,
    ),
    # Evidence-claims: "the tests pass", "all 3 tests pass", "CI is green again",
    # "the build is passing". Three things keep this narrow:
    #   - the noun must be a check (EVIDENCE_NOUNS), so "the light is green" is out;
    #   - only a short list of linking words may sit between the noun and the
    #     result word, so "the tests should pass" / "will pass" / "don't pass" is out;
    #   - the result word must END its clause, so a transitive use with an object
    #     — "the pipeline passes messages downstream" — is out.
    # Lead-ins that make the sentence non-assertive ("If the tests pass, …",
    # "I can't confirm the tests pass") are handled by _is_non_assertive_clause().
    re.compile(
        rf"\b(?:{_EVIDENCE})\b"
        rf"(?:\s+(?:are|is|all|now|again|still|both))*"
        rf"\s+(?:pass(?:es|ed|ing)?|green)\b"
        rf"(?=\s*(?:[.,;:!?)\]\u2014\u2013]|$"
        rf"|\b(?:now|again|still|cleanly|locally|too|both|and|on|in|for|under|after)\b))",
        re.IGNORECASE,
    ),
    # Bolded markers
    re.compile(r"\*\*(?:SHIPPED|DONE|COMPLETE|READY|VERIFIED|LIVE|FIXED|RESOLVED|CLOSED)\*\*"),
    # "verified end-to-end"
    re.compile(r"\bverified\s+end[\s-]to[\s-]end\b", re.IGNORECASE),
)

EXEMPT_CONTEXT = (
    re.compile(r'["“]\s*[^"”]{0,80}\bis\s+(?:done|ready|complete)\b[^"”]{0,80}\s*["”]'),
    re.compile(r"\bwould\s+(?:be|claim|say)\s+(?:is|are)\s+", re.IGNORECASE),
)

# A claim is only a claim when the clause ASSERTS it. Three ways a clause
# fails to, and they do NOT have the same reach, so they are three patterns
# rather than one list.
#
# CONDITIONAL reaches across the whole clause and distributes over coordinated
# ones: in "If the tests pass and the build is green, we ship", the "If"
# governs both halves.
CONDITIONAL_LEAD_IN = re.compile(
    r"\b(?:if|once|when|whenever|unless|until|after|before|assuming|provided|"
    r"whether|should|would|might|may|must|hope|hoping|"
    r"expect(?:ed|ing)?|ensure|ensuring|make\s+sure|so\s+that|"
    r"to\s+(?:see|check|confirm|verify|make|get|ensure))\b",
    re.IGNORECASE,
)
# A conditional interrupted by a parenthetical still governs what follows it:
# the comma in "If, after retries, the tests pass" is punctuation inside the
# conditional, not the start of a new assertion.
PARENTHETICAL_CONDITIONAL = re.compile(
    r"(?:if|once|when|whenever|unless|until|assuming|provided|should|whether)\s*,",
    re.IGNORECASE,
)
# NEGATION binds its own verb phrase only. "I did not change the API and the
# migration is complete." negates the API change, not the migration — so a
# coordinating conjunction ends its reach, which is why COORDINATORS exists.
NEGATION = re.compile(r"(?:\b(?:not|no|never|nor|cannot)\b|\w+n[\u2019']t\b)", re.IGNORECASE)
# ATTRIBUTION hands the claim to someone else and has the same narrow reach.
# The lookahead keeps the SUBJECT nouns out: "The report is complete." and
# "The claims are verified." are claims about a report and some claims, not
# reports and claims about something.
ATTRIBUTION = re.compile(
    r"\b(?:according\s+to"
    r"|(?:says?|said|claims?|claimed|reports?|reported|tells?|told)"
    r"(?!\s+(?:is|are|was|were|has|have|had|will|would)\b))\b",
    re.IGNORECASE,
)
# …except when the source cited is a TOOL the assistant ran. "According to
# pytest the tests pass" is the assistant's own evidence wearing a citation;
# "The contributor says the tests pass" is genuinely someone else's claim.
# Only the second is exempt — the gate exists to make the first one logged.
TOOL_SOURCES = re.compile(
    r"\b(?:pytest|tox|mypy|ruff|eslint|npm|yarn|cargo|make|curl|"
    r"ci|test\s+runner|runner|test\s+run|build|pipeline|suite|workflow|job|"
    r"logs?|output|coverage|linter?|typecheck(?:er)?|terminal|console)\b",
    re.IGNORECASE,
)
COORDINATORS = re.compile(r"\b(?:and|but|so|yet|then|however|although|though)\b", re.IGNORECASE)
# Clause boundaries. Em and en dashes divide clauses as firmly as a comma does
# — without them "I hope this helps — the fix is complete." reads as one
# hoped-for clause and a real claim gets suppressed.
STRONG_BOUNDARIES = ".!?;\n\u2014\u2013"
CLAUSE_BOUNDARIES = STRONG_BOUNDARIES + ":,"


# ---------- EMIT HELPERS ----------
def emit_ok():
    sys.stdout.write('{"continue": true, "suppressOutput": true}\n')
    sys.exit(0)


def emit_warn(msg):
    sys.stdout.write(json.dumps({"continue": True, "systemMessage": msg}) + "\n")
    sys.exit(0)


def emit_block(reason):
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}) + "\n")
    sys.exit(0)


# ---------- TRANSCRIPT READING (with recency guard) ----------
def _parse_ts_as_utc(ts_str):
    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def read_last_assistant_message(transcript_path):
    """Return the most recent assistant message text. Empty string if the
    most recent entry is older than STALE_THRESHOLD_S (transcript-flush race)."""
    p = Path(transcript_path).expanduser()
    if not p.exists():
        return ""
    try:
        lines = p.read_text(errors="ignore").splitlines()
    except OSError:
        return ""
    now_ts = datetime.now(timezone.utc).timestamp()
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        ts_str = entry.get("timestamp")
        if ts_str:
            try:
                if (now_ts - _parse_ts_as_utc(ts_str)) > STALE_THRESHOLD_S:
                    return ""  # stale prior turn; do not block on it
            except (ValueError, AttributeError):
                pass
        msg = entry.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(
                b.get("text", "") for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            )
        return ""
    return ""


# ---------- CLAIM DETECTION + EXEMPTION ----------
def _is_backtick_wrapped(text, m_start, m_end):
    bt_open = text.rfind("`", max(0, m_start - 200), m_start)
    if bt_open == -1:
        return False
    bt_close = text.find("`", m_end, min(len(text), m_end + 200))
    if bt_close == -1:
        return False
    return "`" not in text[bt_open + 1:m_start]


def _is_blockquote_line(text, m_start):
    line_start = text.rfind("\n", 0, m_start) + 1
    i = line_start
    saw_gt = False
    while i < m_start:
        c = text[i]
        if c == ">":
            saw_gt = True
            i += 1
        elif c in (" ", "\t"):
            i += 1
        else:
            break
    return saw_gt


def _ends_in_question(text, m_end):
    # Scan from the match end to the next sentence terminator. If that
    # terminator is "?", the claim sits inside a QUESTION ("Shipped the fix?",
    # "The tests are fixed now?") — not an assertion — so it must not fire.
    for i in range(m_end, min(len(text), m_end + 160)):
        c = text[i]
        if c in ".!?\n":
            return c == "?"
    return False


def _boundary_start(text, m_start, boundaries):
    return max(text.rfind(c, 0, m_start) for c in boundaries) + 1


def _is_attributed(text, span_start, m_start):
    """Whether a reporting verb governs the match. Matched against the FULL
    text from span_start rather than the truncated span, because ATTRIBUTION's
    lookahead needs the verb that follows the candidate word: "report" in
    "The report is complete." is only provably a subject noun by the "is"
    sitting after the match start."""
    for m in ATTRIBUTION.finditer(text, span_start):
        if m.start() >= m_start:
            return False
        return True
    return False


def _is_non_assertive_clause(text, m_start):
    """True if the clause holding the match hedges, negates, or attributes it.

    Hedges reach across the whole clause; negation and attribution stop at a
    coordinating conjunction, because that starts a new assertion. So
    "If the tests pass and the build is green, we ship" stays exempt while
    "I did not change the API and the migration is complete" fires."""
    clause_start = _boundary_start(text, m_start, CLAUSE_BOUNDARIES)
    if CONDITIONAL_LEAD_IN.search(text[clause_start:m_start]):
        return True
    sentence_start = _boundary_start(text, m_start, STRONG_BOUNDARIES)
    if PARENTHETICAL_CONDITIONAL.match(text[sentence_start:m_start].lstrip()):
        return True
    coordinators = list(COORDINATORS.finditer(text[clause_start:m_start]))
    span_start = clause_start + (coordinators[-1].end() if coordinators else 0)
    span = text[span_start:m_start]
    if NEGATION.search(span):
        return True
    return _is_attributed(text, span_start, m_start) and not TOOL_SOURCES.search(span)


def find_claims(text):
    matches = []
    seen = set()
    for pat in CLAIM_PATTERNS:
        for m in pat.finditer(text):
            phrase = m.group(0).strip()
            key = phrase.lower()
            if key in seen:
                continue
            if _ends_in_question(text, m.end()):
                continue
            if _is_non_assertive_clause(text, m.start()):
                continue
            if _is_backtick_wrapped(text, m.start(), m.end()):
                continue
            if _is_blockquote_line(text, m.start()):
                continue
            ctx = text[max(0, m.start() - 80):min(len(text), m.end() + 80)]
            if any(ex.search(ctx) for ex in EXEMPT_CONTEXT):
                continue
            seen.add(key)
            matches.append(phrase)
    return matches[:5]


# ---------- FRESH LOG CHECK ----------
def has_fresh_log(window_min=CLAIM_CHECK_FRESH_MIN):
    if not CLAIM_CHECKS_LOG.exists():
        return False
    try:
        lines = CLAIM_CHECKS_LOG.read_text().splitlines()
    except OSError:
        return False
    now_ts = datetime.now(timezone.utc).timestamp()
    cutoff = now_ts - (window_min * 60)
    for line in reversed(lines[-20:]):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            ts_str = entry.get("timestamp") or entry.get("ts")
            if not ts_str:
                continue
            if _parse_ts_as_utc(ts_str) >= cutoff:
                return True
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
            continue
    return False


# ---------- MAIN ----------
def main():
    mode = os.environ.get("CLAIM_CHECK_ENFORCE_MODE", DEFAULT_MODE).lower()
    if mode == "off":
        emit_ok()

    try:
        hook_data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        emit_ok()

    if hook_data.get("stop_hook_active") is True:
        emit_ok()  # prevent re-block loop

    transcript_path = hook_data.get("transcript_path")
    if not transcript_path:
        emit_ok()

    message = read_last_assistant_message(transcript_path)
    if not message:
        emit_ok()

    claims = find_claims(message)
    if not claims:
        emit_ok()

    if has_fresh_log():
        emit_ok()

    bullets = "\n".join(f'  - "{p}"' for p in claims)
    reason = (
        f"⚠️  Claim-check enforcer — done-claim detected without fresh verification log entry.\n"
        f"Matched phrases:\n{bullets}\n\n"
        f"Last claim_checks/log.jsonl entry is older than {CLAIM_CHECK_FRESH_MIN}min.\n"
        f"Before stopping this turn:\n"
        f"  1. Run a real verification (test, end-to-end check, etc.)\n"
        f"  2. Log it:  python3 log_claim.py \"<what you claim>\" \"<how you verified>\"\n"
        f"  3. Re-reply to the operator\n\n"
        f"Override: CLAIM_CHECK_ENFORCE_MODE=warn or =off"
    )

    if mode == "warn":
        emit_warn(reason)
    emit_block(reason)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # True fail-safe: an unexpected error must NEVER break the operator's turn.
        emit_ok()
