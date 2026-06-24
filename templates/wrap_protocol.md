# Session End Protocol

Mechanical, not aspirational. Same checklist every time.

## Trigger

- Token usage crosses **70-80%** of context window
- OR major milestone hit
- OR operator says "wrap"

Wrap *before* you hit the wall. Whatever isn't durably written when the session ends is gone.

## Steps

### 1. Stop new work

No new explorations, no new builds, no new tools spun up. The remainder of the session is wrap-only.

### 2. Prep the handoff packet

Write `handoff/YYYY-MM-DD-HHMM.md` (or .json — structured is better if you'll parse it):

```markdown
# Handoff — <date> <time>

## What's running
- <PID / process / job> — <what it's doing>

## Shipped this session
- <commit / artifact / decision>

## Next
- <top of queue for next session>

## Blockers / open questions
- <thing the operator needs to decide>

## Files modified
- <path 1>
- <path 2>

## Tests to run before next session starts
- <test invocation>
```

### 3. Update CONTEXT.md

At the project root (or equivalent per-project context file):

- **Running PIDs** section — what's live
- **Done** section — what shipped
- **Next** section — what's queued
- **Blockers** section — what's stuck

### 4. Write to ≥2 durable surfaces

Pick at least two of:

- **Local memory file** — typed by prefix (`project_session_YYYYMMDD.md`, etc). See `MEMORY.md.template`.
- **Retrieval index** — `store_memory` / `store_session_summary` / equivalent vector write.
- **Structured ops board** — Notion, Linear, etc.

**Never let one surface be the sole source of truth.** If one goes down, you should still have the session's work somewhere else.

### 5. Update the memory index

Add a one-line entry to `MEMORY.md` under `RECENT SESSIONS`:

```markdown
- **YYYY-MM-DD — Short title** one-line hook. (→ link to project_session_YYYYMMDD.md)
```

### 6. Git commit + push

If version-controlled. Branch and commit message reflect this session's work, not a generic "wrap" message.

### 7. Surface the next-session command

In the final assistant message, give the operator the literal command to copy-paste to resume:

```bash
# next session start command
cd <project>
cat handoff/YYYY-MM-DD-HHMM.md
```

## Don't

- **Don't append session logs to load-bearing pages** (roadmap / OKR / status docs / etc). Those have governance rules — session logs belong in memory + retrieval, not in the page body.
- **Don't overwrite a parallel session's manifest** if their timestamp is newer than yours. Compare timestamps first; merge if their work is newer.
- **Don't declare "done" while in flow.** If the session ends with three open follow-ups, name them. State what's pending, not just what shipped.
- **Don't skip wrap because the session was short.** Short sessions are the ones whose context evaporates.

## Failure modes

- *Skipped wrap.* Whatever isn't durably written is gone. Treat wrap as non-optional.
- *Single-surface wrap.* One bad day for that surface = full amnesia. Always write to ≥2.
- *Manifest overwrite.* Two sessions wrap concurrently and the later one clobbers the earlier. Fix: compare manifest timestamps before overwrite; merge if existing is newer.
- *Aspirational "I'll remember tomorrow."* You won't. The agent definitely won't.
