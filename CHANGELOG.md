# Changelog

Notable changes to the andon **starter kit**. Loosely follows
[Keep a Changelog](https://keepachangelog.com/). The kit versions independently
of the doctrine in [`docs/THE_OPERATORS_CODE.md`](docs/THE_OPERATORS_CODE.md).

## Unreleased

- **claim-check:** recall fix for the detector (issue #3). Sentence-start forms now
  accept a first-person lead-in (`I've implemented the…`), `implemented` / `finished`
  join the standalone and action lists, and there are new patterns for evidence-claims
  (`the tests pass`, `CI is green`) and subject-noun closures (`Task complete!`). A
  clause-scoped guard keeps conditionals (`If the tests pass, …`) exempt. The 13-example
  set from the issue plus a benign set are checked in as regression tests.
- **claim-check:** precision pass over those new patterns. A clause that negates
  (`I can't confirm the tests pass`), attributes (`the contributor says the tests pass`)
  or hedges a claim no longer fires; `passes` with an object (`the pipeline passes
  messages downstream`) and attributive `live` (`live data`, `live-streaming`) no longer
  fire; em and en dashes now count as clause boundaries, so `I hope this helps — the fix
  is complete.` fires again.

## v0.1.0 — Initial public release

The starter kit: typed memory templates, the **claim-check** Stop hook (catches a
false "done"), **auto-orient** (loads memory at session start), the wrap/orient
loop, lanes, a starter agent team, ready-made slash commands, the Defect Ledger,
and the full doctrine. Plain Markdown + stdlib Python 3 — no dependencies, no
account, no lock-in. Ships in **warn** mode; promote to **block** when you trust it.
