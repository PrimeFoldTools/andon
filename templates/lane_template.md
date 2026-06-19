# Lane assignment: <LANE-NAME>

You're working in the **<lane-name>** lane.

> Copy this file when you spawn a new lane. Edit the placeholders. Templates are *structural* — current state (today's tasks, live cells, counts) lives in `LANES.md` and session handoff files, never hardcoded in the template.

## ⛔ STRICT — ONE SESSION MAX (remove if not applicable)

This lane has a hard exclusivity rule because <reason: capital lives here / production data / irreversible publish surface>.

## Current state (read these before claiming)

- `LANES.md` → <lane-name> → confirm empty before claiming
- <project>/CONTEXT.md → in-flight work
- <state file 1> — <what it tracks>
- <state file 2> — <what it tracks>
- Last 7 days of CLAUDE.md Mistakes Log (grep for lane-relevant keywords)

## Before any work

1. Read `LANES.md` — confirm lane is **empty** before claiming. If claimed by another session, STOP — work a different lane or wait.
2. Read project CLAUDE.md + CONTEXT.md.
3. Read MEMORY.md (auto-loads).
4. Read required REVIEW_QUEUE items (paste paths here).
5. Read current state of <load-bearing config files>.
6. Run `git log --oneline -20` to see recent commits across all sessions.
7. Claim the lane in `LANES.md` with your session id + ISO-8601 timestamp + one-line task.

## Lane scope

<what work belongs in this lane>

- <thing 1>
- <thing 2>
- <thing 3>

## OUT of this lane (do NOT touch)

<what's explicitly forbidden in this lane>

- <thing A> — belongs in <other lane>
- <thing B> — belongs in <other lane>

## Hard gates (if lane touches anything irreversible)

Any <irreversible action: capital flip, production publish, schema change> requires:

1. **Explicit operator authorization in *this* session.** Not from prior session memory.
2. **<validation 1>**
3. **<validation 2>**
4. **End-to-end verify the dependent path** — run the actual notification / publish / write call and confirm it returns success. Don't trust import-success as proof of working pipe.
5. **Cross-source config drift audit** — grep for parallel readers of the same logical config; ensure they all read from the canonical source.

## Hard rules

- **Search before building.** `grep -rn <keyword> --include="*.<ext>"` before authoring new code that overlaps existing functionality.
- **Single atomic patch for state writes.** When promoting / writing across multiple destinations (e.g., index + detail file), write both in the same commit. Schema-sync invariant lives in a test.
- **Lane release sequence:** claim → work → commit (while claimed) → release → `git commit` immediately. Python file-write is atomic at the filesystem layer, NOT at the git layer when ≥2 sessions are committing.
- **Proof of shipped = real state mutation under real runtime conditions.** NOT a unit test, not a parse-check, not an import-success. Real DB INSERT (or equivalent) under the real cron / production env.

## Required tests before any hard-gate flip

```bash
<test invocation 1>
<test invocation 2>
<test invocation 3>
```

All must pass. Any failure blocks the flip.

## Wrap protocol when done

1. **Update LANES.md:** mark lane empty + last-completed line with summary.
2. **Mistakes Log entry** if any drift was caught — even if fixed in-session.
3. **Memory + retrieval index write** — durable record of decisions (especially for capital-adjacent or irreversible lanes).
4. **Verify post-state:**
   - <state 1> matches operator authorization
   - <state 2> matches operator authorization
   - All required test suites still pass
   - Dependent pipe still returns success end-to-end
5. **Don't declare "done" while in flow** — state what's left or what you're pausing on.

## When in doubt — STOP and ask the operator

Irreversible decisions are not reversible without cost. The 30-second cost of asking is cheaper than any wrong move.
