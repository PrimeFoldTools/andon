# Commands — ready-made shortcuts

Drop-in slash commands. Copy any of these into `~/.claude/commands/` (personal — all your projects) or `<project>/.claude/commands/` (one project), and it becomes available as `/<name>`.

| Command | What it does |
|---|---|
| `/wrap` | Run the session-close protocol — save state, update CONTEXT, commit, surface next moves |
| `/orient` | Load project context now — read the memory index + recent state |
| `/log-mistake` | Append a one-line entry to your Mistakes Log |

These are plain prompt files — open them and adapt the wording to your setup. To build your own (with frontmatter + auto-invocation), copy `../templates/skill_template.md` for the richer form.
