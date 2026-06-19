# CLAUDE.md — Habitloop (example)

> A FILLED-IN example so you can see the skeleton in use. Habitloop is a made-up
> habit-tracking web app (Next.js + SQLite). Copy the shape, not the content.

## Operator profile

Solo indie developer building Habitloop, a small habit-tracking web app. Next.js + SQLite,
deployed on a single VPS. Optimize for shipping working features over polish; I'd rather
have 3 solid features than 6 half-done ones. I'm not a strong backend dev — explain DB
decisions in plain terms.

## Search Before Building (MANDATORY)

Before writing any new util, component, or migration: `grep -rn "<name>" src/` and check
`memory/` for a prior decision. If it exists, use it.

## Operating Rules

- I'm the decider. Gates advise; they don't block.
- Be concise. Show me the change, not a wall of explanation.
- No deploy to prod without my explicit "ship it."
- One feature branch at a time. Don't refactor unrelated code in a feature PR.
- Raw SQL, not an ORM (decided — see `memory/feedback_raw_sql_not_orm.md`).

## Session Protocol

**Start:** read `memory/MEMORY.md`, then this file.
**End:** update `memory/MEMORY.md` (one line under Recent), note anything unfinished, commit.

## Mistakes Log

**Format:** `YYYY-MM-DD — symptom. Correction: … Codified: …`

- 2026-05-02 — Claimed the auth migration was applied; it wasn't run. **Correction:** verify before saying done. **Codified:** claim-check hook (warn mode) + log_claim.
- 2026-05-09 — Wrote a second `formatDate()` when one already existed in `src/lib/`. **Correction:** grep before building. **Codified:** Search-Before-Building rule above.

## Token Budget

Keep this file under ~1 page. Detail lives in `memory/` files, loaded on demand.
