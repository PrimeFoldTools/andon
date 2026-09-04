# The Operator's Code

**For people who actually ship — 11 laws and 5 patterns for running Claude Code as an operating system.**

*v3 · final pre-ship pass.*

---

## TL;DR

If you forget everything else:

1. **Make the agent's mistakes un-repeatable.** Log them. Codify them. Prune entries when the codification has held.
2. **Make automated behaviors mechanical.** Hooks beat memory. Settings beat instructions.
3. **Wrap to multiple durable surfaces.** Single-surface state is one bad day away from gone.
4. **The operator decides.** Gates advise. Pipelines draft. Multi-agent consensus is not authorization.

The rest is detail.

---

## Day 1 Setup

Most readers will not implement eleven laws on day one. The two that pay off fastest:

1. **Start a Mistakes Log.** A single section in your `CLAUDE.md` (or equivalent global-instructions file). One line per mistake: date, symptom, correction, codification path. The agent reads it on every session. See Law 2.

2. **Install one Stop-hook enforcer.** Start with the claim-check pattern: block the turn-end if the agent claims "done / shipped / verified" without a verification log entry. The runnable hook is in `hooks/claim_check_hook.py`. See Pattern 4.

One pattern to install at the same time:

3. **A typed memory directory** with `MEMORY.md` as the index and prefixed filenames (`project_*`, `feedback_*`, `reference_*`, `user_*`). The agent reads `MEMORY.md` automatically; the prefixes let `grep` do the work no schema would. See Law 11 + Pattern 3.

That's enough to feel the system working. Add the rest as friction surfaces.

---

## Why this exists

Most people use AI tools the way they used Stack Overflow: ask a question, copy an answer, close the tab. The agents got smarter and the loop didn't change.

If you live inside an agent — building, shipping, researching, writing — the chat-window model breaks fast. The agent forgets. The agent over-claims. The agent rebuilds something that already exists. Two parallel sessions stomp the same file. A "done" claim turns out to be three open follow-ups in a trench coat.

The fix isn't more prompts. The fix is treating the agent like a system you operate: rules, memory, lanes, hooks, gates, wraps, an audit trail.

This is the distillation of one such system — built, broken, re-built, patched across hundreds of sessions. The personal-specific parts are stripped out. What's left are the patterns that transferred.

The audience is anyone running Claude Code (or a similar agent) seriously: parallel sessions, skills + MCPs, the terminal as mission control. You already know the *what*. This is the *how* — the operating discipline that keeps a heavily-used agent system from eating itself.

None of this is invented from nothing. The "agent as a system you operate" framing echoes Karpathy's LLM-OS idea; the spine underneath is Lean manufacturing. "Make the mistake un-repeatable" is *poka-yoke* — Toyota mistake-proofing. The Mistakes Log is a *kaizen* loop. The stop-the-turn hook is an *andon* cord: pull it when a defect appears. My background is 15 years in manufacturing, up to production manager, where we ran on applied Lean and Six Sigma — Paul Akers style, more applied than exact; the whole guide is that discipline applied to agents.

Three parts:

1. **Operating Doctrine** — 11 laws.
2. **Meta-Patterns** — 5 reusable workflows, each with a template.
3. **The Kit** — drop-in templates, hooks, commands, and a starter agent team.

Read once. Steal what fits. Skip the rest.

---

## Part 1 — Operating Doctrine

### 1. Operator-as-CEO

**Rule:** Gates advise. The operator decides.

**Reason:** Mature agent systems accumulate gates — validation steps, safety checks, "are you sure" prompts. Useful, until they start blocking the work the operator explicitly asked for. The fix isn't fewer gates; it's making them advisory. The operator is the only thing that can weigh a gate against context the gate doesn't see.

**Example:** A "freeze" rule pauses non-critical side projects. The agent generalizes "freeze" into a blanket "don't build anything new" and refuses an explicit operator request. The fix: freezes apply to *specific named items*, never as a default posture. The operator's "do this" is always authorization.

**Failure if ignored:** The system trains the operator to fight it. Trust collapses. Eventually the operator turns the gates off entirely.

---

### 2. Mistakes Log

**Rule:** Keep an append-only one-line log of agent mistakes. Each entry has three fields: symptom, correction, codification path.

**Reason:** Agents forget across sessions. A natural-language log read at session start is the cheapest possible memory. The discipline isn't writing entries — it's the **codification** field, which forces the question: *did we make this mistake un-repeatable, or just write it down?*

**Format:**

```
- YYYY-MM-DD — <symptom>. **Correction:** <how to avoid>. **Codified:** <test path / hook / rule file / "not yet">
```

**Example entries you'll write in week one:**

- *Recommended a tool I hadn't checked for free local alternatives.* **Correction:** Check the tool resource library first. **Codified:** new rule in CLAUDE.md "Tool Selection" section.
- *Declared "done" while three follow-ups were still open.* **Correction:** State what's left, not just what shipped. **Codified:** ready-claim-check hook (Pattern 4).

**Consolidation clause.** When the log gets long, ≥3 entries sharing a root cause can collapse into one meta-entry. No lesson lost; only redundancy removed. Cap around 30 active entries; consolidate or prune past that.

**Failure if ignored:** Same mistake every two weeks. Quietly.

---

### 3. Ready-claim-check

**Rule:** No "done / shipped / complete / ready / verified" claim without a concrete verification trail. Make it mechanical, not aspirational.

**Reason:** Agents over-claim. It's the single most expensive failure mode in agent systems — operator trusts a false "done," moves on, and the gap surfaces hours later. Polite reminders don't fix it. A stop-hook that blocks the turn until a verification log entry exists does.

**Mechanism:**

1. Maintain a `claim_checks/log.jsonl` file. Each verified claim writes one line: timestamp, claim text, verification run.
2. Add a Stop hook that scans the last assistant message for done-claim phrases.
3. If a claim is detected and no log entry exists within the last ~15 minutes, block the turn-end.
4. Provide escape hatches via env var.

Verbatim quotes (blockquote prefix, backtick-wrapped citations, operator quote-backs) must be exempted — those aren't the agent's own claims.

Runnable version in `hooks/claim_check_hook.py`. See Pattern 4.

**Failure if ignored:** The agent's "done" stops meaning anything. You stop trusting your own logs.

---

### 4. Search before building

**Rule:** Before writing a new artifact (script, parser, doc, recommendation), run grep + semantic search + memory check. If something exists, use it.

**Reason:** Most "build this" requests have an existing answer. The agent skips the check because the search feels slower than the build. It isn't. A 30-second grep saves three sessions of false-alarm work.

**The four searches:**

1. **Grep the code.** `grep -rn "<keyword>" --include="*.py"` (or your stack's equivalent).
2. **Semantic search** the indexed corpus (Chroma, Pinecone, whatever you have).
3. **Memory check** — read the relevant doctrine/reference file *before* recommending.
4. **Tool library** — does an existing tool already do this? Don't recommend a paid service before checking free alternatives.

If all four come empty, build. Otherwise use what's there.

**Failure if ignored:** Duplicate parsers with subtly different schemas. The most expensive silent-bug class.

---

### 5. Lane discipline

**Rule:** Define a small fixed set of work-lanes. Every session claims a lane before starting. High-blast-radius lanes are single-session-max.

**Reason:** Once you have ≥2 parallel agent sessions, they will race on shared state — config files, registries, databases, anything writable. Lanes prevent races at the social-protocol layer, before the locking-mechanism layer.

**Pattern:**

- A `LANES.md` file lists each lane and its current claim (session id + timestamp + one-line task).
- The first action of any new session: read `LANES.md`, pick a lane, write a claim line.
- For lanes touching capital, production data, or anything irreversible: **one session at a time, period**.

**Lane release sequence:** claim → work → commit (while still claimed) → release → immediate commit of the release. Python file-write is atomic at the filesystem layer; not at the git layer if multiple sessions are committing.

**Failure if ignored:** Two sessions write to the same registry. Dedup-by-string-id silently allows 16 entries for 8 cells. Caught at verify if you're lucky.

---

### 6. Wrap to N places

**Rule:** Every session ends by writing durable state to at least two surfaces: a memory store (markdown/files) and a retrieval index (vector DB / search). Hard-coded paths, not freestyle.

**Reason:** Single-surface state is brittle. If your only memory is the chat history, you're one context-overflow away from amnesia. If your only memory is a vector DB, you're one corruption away from amnesia *and* one schema change away from invisible drift.

Wrap on token-budget crossing 70-80%, not on "feeling done." See Pattern 2 for the full checklist.

**Failure if ignored:** You wake up tomorrow and the agent doesn't remember what it shipped today.

---

### 7. Schema as enforcement

**Rule:** Frontmatter, filename prefixes, and canonical loaders are enforcement, not convention. If the structure isn't checked, it isn't there.

**Reason:** Conventions drift. Every parser written from memory is a divergence opportunity. The cure is making the schema *the thing* — a frontmatter block the loader requires, a filename prefix the indexer reads, a canonical `@dataclass(frozen=True)` that everyone imports.

Three places this earns its keep:

- **Skill files** — YAML frontmatter the loader fails loudly on.
- **Memory files** — prefix-typed filenames the index regex relies on.
- **State files** — one canonical loader for any JSON read by ≥2 modules.

**Failure if ignored:** Four parsers of the same file, each reading fields in a different order. The bug doesn't crash; it silently returns wrong results.

---

### 8. Operator-trust gate

**Rule:** Pipeline output is not the same as operator endorsement. Before any external publish/push, three checks must all pass: artifact-ready, destination-built, operator-confirmed.

**Reason:** Automated pipelines produce *drafts*. The agent will treat its own draft as ship-ready because the pipeline succeeded. It isn't.

The three checks:

1. **Artifact-ready** — internal QA pipeline passed. Necessary, not sufficient.
2. **Destination-built** — the publish target exists. No publishing into the void.
3. **Operator-confirmed** — explicit "yes, publish" from the human. Not implied. Not inferred. Not "they were silent so I went."

Watch for multi-agent pile-on: agent A surfaces an artifact, agent B cites A's surfacing as evidence, agent C cites both. None of them independently validated.

**Failure if ignored:** Something ships the operator wouldn't have approved. Damage is reputational and time-expensive.

---

### 9. Iteration cap

**Rule:** Pre-ship, cap iterations at three versions. Declare v3 the final pass explicitly. Post-ship, iterate freely.

**Reason:** Iteration on a draft is a hiding spot. Each round produces real improvements *and* defers shipping. Internal review can't see this — each iteration is "obviously needed." External eyes catch the meta-pattern: four versions of an 80%-shipped artifact.

- When iteration count crosses three: declare next pass = final pass. Then ship.
- After shipping: live-surface iteration is free.
- When you can't tell if you're improving or hiding: ask an external eye.

**Failure if ignored:** A 90% v3 becomes a 91% v6 that never ships.

---

### 10. Freeze rule with explicit scope

**Rule:** Freezes apply to specific named lists. Default state is *unfrozen*. The operator's "do this" overrides.

**Reason:** Freezes are useful when scoped ("no new content marketing until X") and toxic when generalized ("don't build anything"). The agent will overgeneralize unless the scope is named explicitly and the default is the opposite of the freeze.

Pattern:

- Each freeze names: what's frozen, why, until when, what's *not* frozen.
- The agent's default posture is "build / help / answer." Freeze is the exception.
- The operator's explicit request to do frozen work = the freeze didn't apply, or the operator just lifted it.

**Failure if ignored:** Agent refuses a legitimate request citing a freeze that wasn't about that thing.

---

### 11. Memory as typed index

**Rule:** Memory files use prefix-typed filenames + a single index file. No freestyle names, no orphan files.

**Reason:** A folder of 1,000 markdown files with creative names is a graveyard. A folder of 1,000 markdown files prefixed `project_*`, `feedback_*`, `reference_*`, `user_*` is queryable with grep.

| Prefix | Contents | Lifetime |
|---|---|---|
| `project_*` | Active work, ongoing initiatives, session logs | Days to months |
| `feedback_*` | Operator decisions, locked doctrines, lessons learned | Long-lived |
| `reference_*` | Canonical patterns, playbooks, how-to docs | Long-lived |
| `user_*` | Operator identity, preferences, focus areas | Long-lived |

Index file (`MEMORY.md`): one line per memory file. Sections by topic, not chronology. Keep it short — a long index doesn't get read carefully, and some harnesses truncate large files outright.

**Failure if ignored:** The agent re-derives things it already knows because it can't find them.

---

## Part 2 — Meta-Patterns

### Pattern 1 — Lane template

**Problem:** Multi-session work races on shared state. "Just be careful" doesn't scale past two sessions.

**When to use:** Once you regularly run ≥2 parallel agent sessions, or when one lane touches anything irreversible (capital, production data, public publish surfaces).

**Template** (full version in `templates/lane_template.md`):

```markdown
# Lane assignment: <lane-name>

## ⛔ STRICT — ONE SESSION MAX  (only if applicable)

## Current state (read before claiming)
- LANES.md → <lane-name> → confirm empty
- <state file 1>, <state file 2>
- Last 7 days of Mistakes Log

## Before any work
1. Read LANES.md — claim or wait
2. Read project CLAUDE.md + CONTEXT.md
3. Read required REVIEW_QUEUE items
4. Write claim line: session id + ISO timestamp + one-line task

## Lane scope / OUT of scope

## Hard gates (if irreversible actions live in this lane)

## Wrap protocol when done
1. Mark lane empty + last-completed line
2. Mistakes Log entry if drift caught
3. Memory + retrieval index write
4. Don't declare "done" while still in flow
```

**Key discipline:** Templates are structural. State (current cells, counts, today's blockers) lives in `LANES.md` and session handoff files — not in the template.

**Failure modes:**

- Skip the claim because "I'll be quick." Two sessions write the same registry.
- Release before commit. Parallel session reads the released state, commits over your work. Sequence is non-negotiable.

---

### Pattern 2 — Wrap protocol

**Problem:** Sessions end at token limit. Whatever isn't durably written is gone.

**When to use:** Every session. Trigger on token-budget crossing 70-80%, not on "feeling done."

**Template** (full version in `templates/wrap_protocol.md`):

1. **Stop new work.** No new explorations, no new builds.
2. **Prep a handoff packet** (`handoff/YYYY-MM-DD-HHMM.md`): what's running, what shipped, what's next, blockers, files modified, tests to run.
3. **Update CONTEXT.md** at the project root.
4. **Write to ≥2 durable surfaces:** local memory file (typed prefix) + retrieval index. Optional third: structured ops board.
5. **Update the memory index** — one line under `RECENT SESSIONS`.
6. **Git commit + push.** Branch and message reflect the session's actual work.
7. **Surface the next-session command** — literal copy-paste for the operator.

**Don't:**

- Append session logs to load-bearing pages (roadmap / OKR / status docs). Those have governance rules.
- Overwrite a parallel session's manifest if their timestamp is newer. Compare first; merge if theirs is newer.
- Declare "done" while in flow. State what's pending.

**Failure modes:**

- Skipped wrap because the session "was short." Short sessions are the ones whose context evaporates.
- Single-surface wrap. One bad day for that surface = full amnesia.

---

### Pattern 3 — Memory filing schema

**Problem:** N markdown files in one folder is a graveyard. Without a schema you can't find anything; with too much structure nothing gets filed.

**When to use:** Day one. Establish prefixes before you have 50 files.

**Template:**

```
memory/
├── MEMORY.md                  # Index — one line per file
├── project_*.md               # Active work
├── feedback_*.md              # Operator decisions, doctrine
├── reference_*.md             # Canonical patterns, playbooks
├── user_*.md                  # Operator identity
└── archive/                   # Pre-consolidation versions
```

File frontmatter:

```markdown
---
name: <short title>
description: <one-line, used to decide relevance>
type: <project | feedback | reference | user>
---
```

**Discipline rules:**

- One line per index entry. Under 200 lines total.
- Sections by topic, not chronology.
- Consolidate when the index passes ~150 lines.

**Failure modes:**

- Freestyle filenames. No way to grep by type. Enforce at write-time via hook.
- Index becomes a wall. Too long, and the important entries get buried where they don't get read (some harnesses also truncate).
- Same fact in three files. Run weekly consolidation.

---

### Pattern 4 — Hook-as-enforcer

**Problem:** If a rule has to fire every turn, it doesn't belong in memory. Memory says "remember to do X" and the agent forgets at the worst moment. Hooks fire mechanically. The agent can't forget a hook.

**When to use:** Any rule that must apply every turn — claim-check, link discipline, frontmatter validation, budget warning, lane claim verification.

**Three hook archetypes:**

| Hook | When it fires | What it does |
|---|---|---|
| UserPromptSubmit | Every prompt | Auto-loads relevant context (recent memory, semantic search) before the agent sees the prompt |
| Stop | Turn end | Validates the assistant message before the operator sees it (claim-check, link discipline) |
| PostToolUse | After tool calls | Notifies / logs / re-formats based on what the agent just did |

A runnable Stop-hook is in `hooks/claim_check_hook.py` (with its log-writer `hooks/log_claim.py`). The design rules learned the hard way:

1. **Always provide an escape hatch env var.** When the hook is wrong, the operator needs to override without editing settings.
2. **Recency-guard transcript reads.** Stop hook fires before the just-completed message flushes — guard with a max-age threshold (~30s) and pass-through on stale content.
3. **UTC-aware timestamps everywhere.** Local-time vs UTC drift will silently break your "fresh log" detection.
4. **Exempt verbatim citations.** Operator quoting back, backtick-wrapped phrases, and blockquote lines are not the agent's own claims.
5. **`stop_hook_active` short-circuit.** Prevents re-block loops where the block reason itself triggers another block.
6. **Block reason must include matched phrases + remediation step.** A vague block teaches nothing.
7. **Block schemas are not interchangeable across hook types.** A *Stop* hook blocks with `{"decision": "block"}`; a *PreToolUse* hook blocks with `{"hookSpecificOutput": {"permissionDecision": "deny"}}`. Use the wrong one and your "block" is a silent no-op — false confidence on a safety gate. Verify your harness's current contract before trusting a new hook.

**Registration** (in `settings.json`):

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python3 /absolute/path/to/your_enforcer.py"
      }]
    }]
  }
}
```

If you find yourself writing "always remember to..." in `CLAUDE.md`, it probably wants to be a hook.

**Failure modes:**

- No escape hatch. Operator can't bypass a wrong-positive. Frustration peaks fast.
- No recency guard. False fires on stale prior-turn content. Operator stops trusting the hook.
- Vague block reason. The operator can't tell why they were blocked.

---

### Pattern 5 — Multi-pass copy pipeline

**Problem:** AI-drafted text has tells. Even when "good," it reads predictable. Single-pass editing doesn't fix the underlying patterns.

**When to use:** Any external-facing copy.

**Template** (branch by content type):

```
RAW DRAFT
    │
    ├─→ de-slop            (remove AI patterns, predictable phrasings)
    │
    ├─→ [branch by type]
    │     ├─ creative/marketing → humanize  (add voice, specificity, soul)
    │     └─ factual/technical  → de-tell   (remove structural AI tells, preserve facts)
    │
    ├─→ voice pass         (apply your voice — encoded biases, argument patterns)
    │
    └─→ platform pass      (final pass: tighten, sharpen, structure for the platform)
        │
        ↓
   PUBLISHABLE COPY
```

**Why four passes:**

- One pass conflates concerns. You can't simultaneously remove AI tells, add voice, and structure for the platform.
- Each pass has one job. Outputs are cleaner because the next pass starts from a known state.
- Branching by content type matters: the humanize pass adds soul (great for marketing, wrong for precision data). The de-tell pass removes tells without adding anything (great for technical, sterile for marketing).

The four passes can be four prompts, four agents, four sub-skills, or one long prompt with explicit phase markers. Mechanism doesn't matter; sequencing does.

**Failure modes:**

- Collapse to one pass. Loses the discipline. Predictably mid output.
- Same pipeline for all content. The humanize pass on precision/technical data = soft language where exactness matters.
- Sanitize voice in the name of "polish." External review pushes toward neutral; catch this. Apply structural feedback, reject voice flattening.

---

## One mistake, end-to-end

The doctrine is easier to see in motion. This is one full arc from a mistake to its silence — the kind of loop the system is designed to produce.

**The original incident.** In a single twelve-hour session, the agent declared "wrap complete," "calling it," and "genuinely done" four separate times — then kept working another 30-60 minutes after each declaration. False finality manufactured a stopping point that didn't exist. The operator's sense of where the session was got actively misled.

**First codification: the skill.** A `ready-claim-check` skill was added — a short routine the agent had to invoke before any done-claim. Memory entry referenced it. CLAUDE.md mentioned it.

**Why that wasn't enough.** Two weeks later, the same shape recurred. The skill was aspirational. The agent forgot to invoke it at the moment it most needed to.

**Second codification: the hook.** A Stop hook was added — `claim_check_hook.py` (the one that ships in `hooks/`). It read the last assistant message, scanned for done-claim phrases ("ready," "shipped," "verified," "X has been resolved," "gap closed"), checked a `claim_checks/log.jsonl` for a verification entry within the last 15 minutes, and stopped the turn-end if a claim was detected without a fresh log entry. It started block-by-default; the shipped version is warn-first (a nudge), promotable with `CLAIM_CHECK_ENFORCE_MODE=block` — or `=off` to silence.

**The iterations that followed.** The hook needed three real fixes before it stabilized:

- *Transcript-flush race.* The Stop hook fired before the just-completed assistant message flushed to the transcript. The hook read the *previous* turn's message and blocked on it. Fix: recency guard on the timestamp — skip if the entry is older than 30 seconds.
- *Timezone drift.* The freshness check parsed naive ISO timestamps as local time when they were intended as UTC. On Eastern machines, "fresh" entries drifted 4–10 hours into the "stale" bucket. Fix: parse all timestamps as UTC, consistently, on both read and write.
- *Verb-pattern overreach.* The first regex caught "ARCHIVED 2026-05-17" but missed "the gap has been closed." Extended to handle adverb + auxiliary slots, ID-prefixed nouns, blockquote-line exemption for verbatim quotes.

**The result.** Entries in the Mistakes Log for that specific class went silent. Not because the agent got smarter — because ignoring the hook has to be deliberate now; it can't happen by accident.

**What the arc demonstrates:**

- Doctrine (Mistakes Log) catches the incident.
- A skill (aspirational) is necessary but not sufficient.
- A hook (mechanical) is what actually closes the loop.
- Iteration on the hook is normal; the iterations themselves get logged and codified.

Every law in this guide has an arc like that behind it. The arcs are what produce the laws.

---

## Part 3 — The Kit

This repo *is* the kit. Drop in the pieces you want, edit the placeholders, and you're operating. The layered on-ramp (start with memory, add the rest as you feel the friction) is in [QUICKSTART.md](../QUICKSTART.md); the full file map is in the [README](../README.md). In short:

- `templates/` — `CLAUDE.md` · `MEMORY.md` · `LANES.md` · `CONTEXT.md` · `lane` · `skill` · `wrap_protocol` (fill-in-the-blank).
- `hooks/` — `claim_check_hook.py` (catches false "done") + `auto_orient.py` (loads memory at session start) + `log_claim.py` (+ tests).
- `commands/` — drop-in slash commands: `/wrap` · `/orient` · `/log-mistake`.
- `agents/` — a starter team of role briefs: researcher · auditor · memory-steward · builder · chief-of-staff.
- `scripts/` — `memory_rotate.py` (keeps the index from bloating).
- `examples/` — a filled-in sample project, so you see the shape in use.

The kit is intentionally small per piece. The point isn't a finished system — it's a clean skeleton you grow into the shape of your own work. Start with one `MEMORY.md` (5 minutes); add a hook when an over-claim burns you; add lanes when you run two sessions at once.

---

If you build your own and a pattern here saves you a session — tell me what you stripped, what you kept, what you added. That's how the next version gets honest.

— *The Operator's Code,* drafted from one operator's working system.
