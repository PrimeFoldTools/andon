# Andon

**Stop fixing the same AI mistake twice.**

A Lean *quality system* for AI-assisted work — every defect becomes a permanent countermeasure. Built by a manufacturing operator, for people who actually ship.

![License: MIT](https://img.shields.io/badge/License-MIT-black.svg) ![Status: v1](https://img.shields.io/badge/status-v1-blue.svg)

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

1. In your project, make a memory folder and an index:

   ```bash
   mkdir -p memory
   cp /path/to/andon/templates/MEMORY.md.template memory/MEMORY.md   # path to where you cloned andon
   ```

2. Add 2–3 lines to `memory/MEMORY.md` — the durable facts your agent keeps forgetting (the stack, the rule, the decision).
3. Point your agent at it (e.g. in your `CLAUDE.md`: *"Read `memory/MEMORY.md` at the start of every session."*).

That's Layer 1. Full path in [QUICKSTART.md](QUICKSTART.md).

---

## See it work — the andon cord catching a false "done"

```text
You:    Add the auth migration.
Agent:  Done — the migration is complete and the tests are fixed. ✅

        ⛔ andon — a "done" claim with nothing verified on record.
           matched: "is complete"  ·  "are fixed"
           run the check, log it, then tell me again.

Agent:  You're right — I hadn't actually run them.
        Ran the suite: 2 failures. Fixing those first.
```

That's the claim-check hook (Law 3). It reads the agent's "done" and asks for evidence before the turn can end. Starts in **warn** mode (a nudge); promote to **block** once you trust it. → [HOOK_INSTALL.md](HOOK_INSTALL.md)

---

## Proof — the Defect Ledger

This system came from real defects, logged and closed one at a time. [`DEFECT_LEDGER.md`](DEFECT_LEDGER.md) is the running record: **defect → root cause → countermeasure → result.** It's the part nobody can copy — it's accumulated, not invented. Read a few entries; you'll recognize your own week.

---

## Why this, and not the 20 other memory repos

Be honest: "give your agent memory + a mistakes log" is a crowded idea in 2026. Some tools even auto-capture your corrections into a rule file (e.g. [claude-reflect](https://github.com/BayramAnnakov/claude-reflect)). If you just want memory, use one of those — they're good.

andon is a different thing: **a complete operating discipline, not a memory tool** — built on the one body of knowledge that already solved "stop defects from recurring" 50 years ago, the Toyota Production System.

- **It's the whole line, not one organ.** Memory + the wrap/orient loop + the claim-check cord + lanes + a starter agent team + the doctrine — one opinionated system with a 5-minute on-ramp.
- **A defect closes with a *countermeasure*, not a note.** Writing the mistake down isn't the fix — the fix is a hook or test that makes the whole class impossible (*poka-yoke*). That's the factory difference between "we'll try to remember" and "it can't happen again." The [Defect Ledger](DEFECT_LEDGER.md) is where you see it.
- **It's from someone who ran the floor.** Not a framework reasoned from first principles — 50-year-old manufacturing discipline, ported to agents by someone who lived it.

If that frame resonates, the rest is the proof. If it doesn't, one of the lighter memory repos will serve you better — no hard feelings.

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

The full thinking — 11 laws + 5 patterns + one worked mistake-to-countermeasure arc — is in **[docs/THE_OPERATORS_CODE.md](docs/THE_OPERATORS_CODE.md)**. Read it when you want the *why*; the templates above are the *what* and you can start without it.

---

## Who made this / staying in touch

I'm a manufacturing-and-operations person who ended up running a one-person company inside Claude Code, and codified everything that kept breaking. This is that system, stripped of my private work. It builds on a lot of other people's tools — see [stand-on-these-shoulders.md](docs/stand-on-these-shoulders.md).

If a pattern here saves you a session, I'd genuinely like to hear what you stripped, kept, or added — open an issue. I write more about running AI systems like a production line at **[Hidden Heuristics](https://hiddenheuristics.substack.com)** — no gate, subscribe if you want more.

**Status:** shared as-is and maintained as time allows — a one-person side-release. Issues and PRs are welcome (I read them), just don't expect enterprise SLAs. Fork freely.

*MIT licensed. Free. Adapt it to your own work.*
