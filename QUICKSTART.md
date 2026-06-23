# Quickstart

Four layers. Each one stands on its own — stop whenever it's enough. The whole thing is plain Markdown + a couple of stdlib-only Python hooks.

**Prerequisite:** an agent harness that reads a project instructions file and can run hooks. Written for **Claude Code** (which creates `~/.claude/` when you install it). If you use Cursor / Cline / Windsurf, the templates still apply — your instructions file and hook mechanism just have different names (see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)).

Clone or download this repo first; commands below assume you're inside it.

---

## Layer 1 — Memory (5 minutes, no code)

Stops your agent from re-learning your project every session.

```bash
cd /path/to/your-project
mkdir -p memory
cp /path/to/andon/templates/MEMORY.md.template memory/MEMORY.md
```

1. Open `memory/MEMORY.md`. Add 2–3 lines under the index — the durable facts your agent keeps forgetting (your stack, a hard rule, a decision you made and why).
2. Tell your agent to read it. In your project instructions file (Layer 2, or just a one-liner for now): *"Read `memory/MEMORY.md` at the start of every session."*

Done. From the *next* session on, your agent starts with this context already loaded — the change shows up when it next reads the file, not the instant you save it.

**Filing convention** (so a folder of notes stays searchable instead of becoming a graveyard): name files by prefix —
`project_*` (active work) · `feedback_*` (decisions/lessons) · `reference_*` (how-tos) · `user_*` (who you are).
`MEMORY.md` is the one-line-per-file index. See [examples/sample-project/](examples/sample-project/) for a filled-in version.

---

## Layer 2 — Instructions + a Mistakes Log (20 minutes)

Stops your agent from repeating mistakes you've already corrected.

```bash
cp /path/to/andon/templates/CLAUDE.md.template ./CLAUDE.md   # or ~/.claude/CLAUDE.md for global
```

1. Fill in the **Operator profile** and **Operating Rules** (the template tells you what goes where).
2. Keep the **Mistakes Log** section. The rule: when the agent gets something wrong, add one line — *symptom · correction · how it's now prevented.* The agent reads this every session and stops repeating that class of mistake.

That's the cheapest memory you'll ever build.

---

## Layer 3 — The claim-check hook (30 minutes)

Makes "done" mean something. Full walkthrough in [HOOK_INSTALL.md](HOOK_INSTALL.md) — it covers installing in **warn mode first**, testing that it fired, and turning it off. Short version:

```bash
cp /path/to/andon/hooks/claim_check_hook.py ~/.claude/hooks/
cp /path/to/andon/hooks/log_claim.py        ~/.claude/hooks/
```

Then register it as a Stop hook (warn mode) and tell your agent to log verified claims with `log_claim.py`. → [HOOK_INSTALL.md](HOOK_INSTALL.md)

---

## Layer 4 — When you run parallel sessions

Once you have ≥2 agent sessions going at once, add **lanes** (`templates/LANES.md.template`) so they don't stomp each other, a **wrap protocol** (`templates/wrap_protocol.md`) so no session ends without saving state, and — if you're deep in it — MCP servers and scheduled agents. The full doctrine for all of this is [docs/THE_OPERATORS_CODE.md](docs/THE_OPERATORS_CODE.md).
