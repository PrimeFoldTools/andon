---
description: Close the session — save state to memory, update CONTEXT, commit, surface next moves.
---

Run the session-wrap protocol (full version in `templates/wrap_protocol.md`):

1. **Stop new work** — the rest of this turn is wrap-only.
2. **Write a handoff note** — what's running, what shipped, what's next, blockers, files touched.
3. **Update `CONTEXT.md`** — Running / Done / Next / Blockers.
4. **Write durable state to ≥2 surfaces** — a typed memory file + your retrieval/index (or git + a second local file if you have no vector store).
5. **Add one line to `MEMORY.md`** under Recent.
6. **Commit + push.**
7. **Print the exact command to resume** next session.

Do NOT declare "done" while work is still in flow — name what's pending.
