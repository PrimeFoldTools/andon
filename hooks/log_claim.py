#!/usr/bin/env python3
"""
log_claim.py — write the verification entry that claim_check_hook.py looks for.

Run this right AFTER you actually verify a done-claim:

    python3 log_claim.py "what you claimed" "how you verified it"

It creates ~/.claude/state/claim_checks/log.jsonl on first run, so the very first
claim doesn't get blocked by a missing file/dir. Override the location with the
CLAIM_CHECKS_LOG_PATH env var (must match the hook's).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CLAIM_CHECKS_LOG = Path(
    os.environ.get(
        "CLAIM_CHECKS_LOG_PATH",
        str(Path.home() / ".claude" / "state" / "claim_checks" / "log.jsonl"),
    )
).expanduser()


def main():
    claim = sys.argv[1] if len(sys.argv) > 1 else ""
    verification = sys.argv[2] if len(sys.argv) > 2 else ""
    if not claim or not verification:
        print(
            'usage: python3 log_claim.py "<what you claim>" "<how you verified it>"',
            file=sys.stderr,
        )
        sys.exit(2)

    CLAIM_CHECKS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "claim": claim,
        "verification": verification,
    }
    with CLAIM_CHECKS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"logged → {CLAIM_CHECKS_LOG}")


if __name__ == "__main__":
    main()
