# Incoming Inspection

How changes from outside get into this repo — written down so it's a procedure,
not a mood. The same reason a receiving dock has a check sheet.

On a factory floor, parts from a supplier don't go straight to the line. They
pass incoming inspection: a fixed check sheet, applied the same way every time,
before the parts touch anything. A pull request is the same object — work from
outside, offered, not yet accepted. Nothing enters `main` until **Merge** —
but note the dock is not inert: opening a PR is itself an event, and CI runs
the contributor's code once a run is approved. That is why reading comes
before running.

## The check sheet

Every PR, in order:

1. **One concern per PR.** One bug, one doc fix, one behavior change. A mixed

   diff is unreviewable, and unreviewable is a reject at the dock — ask for a
   split, don't inspect harder.

2. **Read the diff before anything runs.** Correctness and safety are

   different inspections, and safety comes first because CI executes the
   contributor's code. The safety pass asks: does this diff do anything beyond
   what the PR description says? Network calls, writes outside the repo,
   subprocess use, new dependencies, obfuscated strings? Changes under
   `.github/` (workflows, permissions) get the same scrutiny — CI config is
   code that runs with the repo's credentials. Only after this read should a
   first-time contributor's held workflow run be approved. The hooks are
   stdlib-only on purpose — a new dependency is an issue-first conversation
   (see [CONTRIBUTING](../CONTRIBUTING.md)).

3. **CI must be green.** The test suite runs on every PR

   (`.github/workflows/tests.yml`), with read-only repo permissions and
   non-persisted credentials. Red = inspection stops. No exceptions,
   including for the maintainer.

4. **Behavior changes carry tests.** A regression test is the part of a diff

   that argues for itself — but read the tests too: a test that asserts
   nothing is green as well. Green CI is evidence for the inspection, not
   the inspection.

5. **Questions in the open.** "What does this line do?" asked in the PR thread

   is normal inspection, not a gap in the inspector. The answer becomes
   documentation.

6. **Merge is the acceptance stamp.** Everything before it is inspection. A

   bad merge is one revert away — for the code. A revert cannot un-publish a
   leaked secret or undo an external side effect, which is why the safety
   pass happens before anything runs, not after.

## What acceptance costs

Every merged change is something this project now maintains — solo, with no
response-time guarantees (see CONTRIBUTING's maintainer note). So the check
sheet carries a bias:

- Defect fixes and tests **tend to reduce** the maintenance load — a brittle

  test or a poor fix adds to it, so the check sheet still applies. Default:
  welcome.

- New features **add** load, forever. Default: an issue first — and "no thanks"

  is a complete sentence.

Scope creep, not bad code, is how a small tool dies.

---

*This file is itself a countermeasure: the defect was inspecting incoming work
from memory and mood each time; the countermeasure is a standing check sheet.
The ledger's four-part shape, applied to the repo's own process.*
