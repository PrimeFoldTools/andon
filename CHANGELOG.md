# Changelog

Notable changes to the andon **starter kit**. Loosely follows
[Keep a Changelog](https://keepachangelog.com/). The kit versions independently
of the doctrine in [`docs/THE_OPERATORS_CODE.md`](docs/THE_OPERATORS_CODE.md).

## Unreleased

- **claim-check:** better recall on ordinary done-claims (issue #3), as a strictly
  additive change. Sentence-start forms accept a first-person lead-in (`I've implemented
  the…`); `implemented` and `finished` join the standalone list; `in place` and `wired up`
  join `COMPLETION_VERBS`; `live` joins them with its own terminal guard so `live data`
  and `live-streaming` stay quiet; and a subject-noun pattern catches `Task complete!`.
  Nothing the detector previously caught stops being caught — `hooks/tests/test_claim_corpus.py`
  asserts that over the whole accumulated example set. Evidence-claims (`the tests pass`,
  `CI is green`) are deliberately NOT matched: doing so needs assertion-context
  exemptions, and those exemptions are what suppressed real claims in review.

## v0.1.0 — Initial public release

The starter kit: typed memory templates, the **claim-check** Stop hook (catches a
false "done"), **auto-orient** (loads memory at session start), the wrap/orient
loop, lanes, a starter agent team, ready-made slash commands, the Defect Ledger,
and the full doctrine. Plain Markdown + stdlib Python 3 — no dependencies, no
account, no lock-in. Ships in **warn** mode; promote to **block** when you trust it.
