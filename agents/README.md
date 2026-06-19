# Agent roles — your starter team

> *Honest note: this is the most generic part of andon — every AI setup grows some version of these, so they're useful utilities, not the headline. The differentiated version (roles shaped around **failure modes** — a Claim Checker, a Defect Investigator, a Reality Auditor) is on the roadmap. For now, a practical starting team.*

These are role briefs for **subagents** you delegate to. In Claude Code you spawn a subagent and hand it one of these as its instructions; it works in its own context and reports back. The point: don't make one agent do everything in one thread — give specialized work to specialized roles and keep your main thread clean.

Five to start:

| Role | One job | File |
|---|---|---|
| **Researcher** | Gather, read, map. Returns findings, not decisions. | [researcher.md](researcher.md) |
| **Auditor** | The skeptic. Finds what's wrong before you commit. | [auditor.md](auditor.md) |
| **Memory Steward** | Keeps the memory index clean and honest. | [memory-steward.md](memory-steward.md) |
| **Builder** | Implements against a spec; searches first; locks fixes with tests. | [builder.md](builder.md) |
| **Chief of Staff** | Prioritizes and sequences. Surfaces the next move; never decides for you. | [chief-of-staff.md](chief-of-staff.md) |

Each file is a drop-in brief — adapt the wording to your work. The golden rule across all of them (Law 1, *Operator-as-CEO*): **they advise and execute; you decide.** None of them is allowed to treat its own output as the final word.
