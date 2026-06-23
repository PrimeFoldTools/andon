# Andon

**Stop fixing the same AI mistake twice.**

A Lean *quality system* for AI-assisted work — every defect becomes a permanent countermeasure. Built by a manufacturing operator, for people who actually ship.

![License: MIT](https://img.shields.io/badge/License-MIT-black.svg) ![Kit: v1](https://img.shields.io/badge/kit-v1-blue.svg)

> *Andon* is the cord on a Toyota line you pull to stop production when something's wrong. This is that cord for AI work: catch the defect, fix it once, and make it un-repeatable.

---

## The problem

If you work inside an AI agent every day, you know the failure modes:

- It **forgets** what you decided last week.
- It **repeats** mistakes you already corrected.
- It says **"done"** when it isn't.
- Projects **drift** — two sessions stomp the same file, context evaporates, you re-explain the same thing.

Most "AI tips" make the *output* a little better. None of them stop the *defects from recurring*.

**The fix isn't a better prompt. It's an operating discipline — borrowed from a factory floor.** On a Lean line, every defect becomes a permanent countermeasure so it can't happen twice. Andon does that for AI work: each mistake becomes a logged defect → a countermeasure → and where it matters, a mechanical guard the agent *can't* skip.

The result: **every project gets a little smarter, and stays that way.**

---

## Quickstart — your first win in 5 minutes (no code)

The smallest useful piece is a structured memory file — so you can come back to a project after three months and your agent knows exactly where you left off, instead of rebuilding context from scratch.

0. Clone this repo first (you'll copy a couple of files out of it):

   ```bash
   git clone https://github.com/PrimeFoldTools/andon.git
   ```

1. In your project, make a memory folder and an index:

   ```bash
   mkdir -p memory
   cp /path/to/andon/templates/MEMORY.md.template memory/MEMORY.md   # path to where you cloned andon
   ```

2. Add 2–3 lines to `memory/MEMORY.md` — the durable facts your agent keeps forgetting (the stack, the rule, the decision).
3. Point your agent at it (e.g. in your `CLAUDE.md`: *"Read `memory/MEMORY.md` at the start of every session."*).

That's Layer 1. The payoff shows up the *next* time your agent starts — it reads the file instead of re-asking, so there's nothing flashy to watch right now. Want an instant, visible win instead? Run the 30-second hook demo below. Full path in [QUICKSTART.md](QUICKSTART.md).

---

## See it work — the andon cord catching a false "done"

The claim-check hook reads the agent's own "done" and asks for evidence before the turn can end. Below is the **verbatim** `systemMessage` the Stop hook emits when a "done" lands with no fresh verification on record — not a mock-up; you can reproduce it in 30 seconds (next block):

```text
You:    Add the auth migration.
Agent:  Done — the migration is complete and the tests are fixed. ✅

⚠️  Claim-check enforcer — done-claim detected without fresh verification log entry.
Matched phrases:
  - "is complete"
  - "are fixed"

Last claim_checks/log.jsonl entry is older than 15min.
Before stopping this turn:
  1. Run a real verification (test, end-to-end check, etc.)
  2. Log it:  python3 log_claim.py "<what you claim>" "<how you verified>"
  3. Re-reply to the operator

Override: CLAIM_CHECK_ENFORCE_MODE=warn or =off

Agent:  You're right — I hadn't actually run them.
        Ran the suite: 2 failures. Fixing those first.
```

That's the claim-check hook (Law 3). It starts in **warn** mode (a nudge); promote to **block** and the turn won't end on an unverified "done." → [HOOK_INSTALL.md](HOOK_INSTALL.md)

### Reproduce it in 30 seconds

From inside the cloned repo — no install, no config:

```bash
printf '{"type":"assistant","timestamp":"%s","message":{"content":"the migration is complete and the tests are fixed"}}\n' \
  "$(python3 -c 'import datetime; print(datetime.datetime.now(datetime.timezone.utc).isoformat())')" > /tmp/t.jsonl

echo '{"transcript_path":"/tmp/t.jsonl"}' \
  | CLAIM_CHECK_ENFORCE_MODE=warn CLAIM_CHECKS_LOG_PATH=/tmp/none.jsonl python3 hooks/claim_check_hook.py
```

You get back the exact `systemMessage` shown above. (Or run the suite: `python3 -m pytest hooks/tests/` — 28 tests.)

*Not ready to install a hook? Layer 1 above — a plain memory file, no code — is the on-ramp. Start there and climb when you feel the friction.*

---

## The Defect Ledger — accumulated, not invented

The runnable proof is the 30-second demo above. The part nobody can copy is the *record*: [`DEFECT_LEDGER.md`](DEFECT_LEDGER.md) logs real defects one at a time — **defect → root cause → countermeasure → result** — where the countermeasure is a hook or test that makes the whole class hard to repeat, not a note that asks you to remember. Accumulated, not invented. Read a few entries; you'll recognize your own week.

---

## Why this, and not the 20 other memory repos

Be honest: "give your agent memory + a mistakes log" is a crowded idea in 2026. Some tools even auto-capture your corrections into a rule file (e.g. [claude-reflect](https://github.com/BayramAnnakov/claude-reflect)). If you just want memory, use one of those — they're good.

andon is a different thing: **a complete operating discipline, not a memory tool** — built on the one body of knowledge that already solved "stop defects from recurring" 50 years ago, the Toyota Production System.

- **It's the whole line, not just memory.** Memory + the wrap/orient loop + the claim-check cord + lanes + a starter agent team + the doctrine — one opinionated system with a 5-minute on-ramp.
- **A defect closes with a *countermeasure*, not a note.** Writing the mistake down isn't the fix — the fix is a hook or test that makes the whole class impossible (*poka-yoke*). That's the factory difference between "we'll try to remember" and "it can't happen again." The [Defect Ledger](DEFECT_LEDGER.md) is where you see it.
- **It's from someone who ran the floor.** Not a framework reasoned from first principles — 50-year-old manufacturing discipline, ported to agents by someone who lived it.

If that frame resonates, the rest is the proof. If it doesn't, one of the lighter memory repos will serve you better — no hard feelings. (Full credit + a reading list of the tools and ideas andon stands on: [stand-on-these-shoulders.md](docs/stand-on-these-shoulders.md).)

---

## What's inside

```text
andon/
├── README.md            ← you are here
├── QUICKSTART.md        ← the 5-minute first win, step by step
├── DEFECT_LEDGER.md     ← real defects → countermeasures → results (the proof)
├── HOOK_INSTALL.md      ← install the two hooks (warn-first, with a "turn it off")
├── TROUBLESHOOTING.md   ← when something doesn't fire / fires too much
├── AGENTS.md            ← point your AI agent at this and it self-installs andon
├── templates/           ← drop-in: CLAUDE.md · MEMORY.md · LANES.md · CONTEXT.md · lane · skill · wrap
├── hooks/               ← claim_check_hook.py (catches false "done") · auto_orient.py (loads memory at start) · log_claim.py · tests
├── commands/            ← ready-made slash commands: /wrap · /orient · /log-mistake
├── agents/              ← a starter team: researcher · auditor · memory-steward · builder · chief-of-staff
├── scripts/             ← memory_rotate.py (keeps the index from bloating)
├── examples/            ← a FILLED-IN sample project (not empty placeholders)
└── docs/
    ├── THE_OPERATORS_CODE.md        ← the full doctrine: 11 laws + 5 patterns
    ├── integrations.md              ← wiring to Obsidian / vector search / Notion
    └── stand-on-these-shoulders.md  ← the tools + repos this builds on
```

Everything is plain Markdown + a few stdlib-only Python scripts (two hooks + a helper). No dependencies, no account, no lock-in.

---

## The four layers — take only what you need

Nothing past Layer 1 is mandatory. Climb when you feel the friction the next layer fixes.

| Layer | You add | Time | Fixes |
|---|---|---|---|
| **1 — Memory** | `MEMORY.md` + a typed memory folder | 5 min | The agent forgetting your project |
| **2 — Instructions** | `CLAUDE.md` + a Mistakes Log | 20 min | Repeating corrected mistakes |
| **3 — The hooks** | claim-check (catches false "done") + auto-orient (loads memory at start) | 30 min | False "done" + starting amnesiac |
| **4 — Operator system** | the agent team · lanes · commands · integrations | when you run parallel sessions | Drift + collisions at scale |

---

## Lean → builder translation

The doctrine is Toyota Production System applied to agents. You don't need the vocabulary to use it — but here's the map:

| Lean / TPS | In plain terms | Where it shows up here |
|---|---|---|
| **Andon** | stop the line when a defect appears | the claim-check hook halting a false "done" |
| **Poka-yoke** | mistake-proofing — make the error impossible, don't rely on memory | hooks > "remember to…" |
| **Kaizen** | a countermeasure for every defect | the Mistakes Log + Defect Ledger |
| **Standard work** | one documented best way | the templates + memory schema |
| **Jidoka** | automated defect detection | the Stop / PreToolUse hooks |
| **Genchi genbutsu** | go and see — don't trust the report | verify the real result, not the log |

---

## The doctrine

The full thinking — 11 laws + 5 patterns + one worked mistake-to-countermeasure arc — is in **[docs/THE_OPERATORS_CODE.md](docs/THE_OPERATORS_CODE.md)** (the doctrine carries its own version — currently v3; this starter kit is v1, and they version independently). Read it when you want the *why*; the templates above are the *what*, and you can start without it.

---

## Who made this / staying in touch

I spent years on a manufacturing floor running Lean — andon cords, poka-yoke, kaizen, standard work — before I ended up running a one-person company inside Claude Code. When the same AI mistakes kept recurring, I reached for the body of knowledge that already solved "stop defects from coming back" 50 years ago and ported it to agents. This repo is that system, stripped of my private work. It stands on a lot of other people's tools — see [stand-on-these-shoulders.md](docs/stand-on-these-shoulders.md).

If a pattern here saves you a session, I'd like to hear what you stripped, kept, or added — open an issue. I write more about running AI systems like a production line at **[Hidden Heuristics](https://hiddenheuristics.substack.com)** — no gate.

**Status:** I run this every day on my own work, so it gets fixed when it breaks. One-person release — issues and PRs welcome (I read them), no enterprise SLAs. Fork freely.

*MIT licensed. Free. Adapt it to your own work.*
