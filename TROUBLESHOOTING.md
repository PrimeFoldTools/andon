# Troubleshooting

## The hook blocks (or warns on) every turn

Two usual causes:

1. **The log is never written.** The hook checks `~/.claude/state/claim_checks/log.jsonl`; if your agent never runs `log_claim.py`, no claim is ever "fresh." Add the logging instruction to your `CLAUDE.md` (see [HOOK_INSTALL.md](HOOK_INSTALL.md) step 4).
2. **A verb is too common in your writing.** Edit `COMPLETION_VERBS` at the top of `claim_check_hook.py` and remove the offender. Start in `CLAIM_CHECK_ENFORCE_MODE=warn` so a false-fire never actually stops you.

Escape hatch any time: `CLAIM_CHECK_ENFORCE_MODE=off`.

## The hook never fires

- **Wrong path.** `~` doesn't expand inside the JSON command string — use the absolute path. Confirm with the step-3 smoke test in [HOOK_INSTALL.md](HOOK_INSTALL.md).
- **Broke `settings.json`.** If you pasted a second top-level `"hooks"` key instead of merging into the existing `"Stop"` array, the JSON is invalid and *all* hooks stop. Validate: `python3 -c "import json; json.load(open('$HOME/.claude/settings.json'))"`.
- **`python3` not found.** Use the full interpreter path if needed (`which python3`).

## MEMORY.md isn't being loaded

- **Wrong location**, or **the agent was never told to read it.** Auto-loading is harness-specific; the reliable move is an explicit line in your `CLAUDE.md`: *"Read `memory/MEMORY.md` at the start of every session."*
- **The index got too long.** If it's hundreds of lines, the important entries are buried (and some harnesses truncate). Keep it to one line per file; move detail into the per-file memory docs.

## I'm not on Claude Code (Cursor / Cline / Windsurf / …)

- **Templates (`CLAUDE.md`, `MEMORY.md`, lanes, wrap):** fully portable — they're just Markdown. Put `CLAUDE.md`'s content into your harness's rules/instructions file.
- **The hook:** depends on whether your harness exposes a turn-end ("stop") hook. If it doesn't, you can still run the discipline manually (a "ready-claim-check" routine you invoke before saying done) — you just lose the mechanical enforcement.

## The hook output looks like raw JSON in my terminal

That's expected — it's a hook protocol message, meant for the harness, not for you to read directly. You only see it when running the smoke test by hand.
