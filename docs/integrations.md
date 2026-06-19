# Integrations — wiring andon to your other tools

andon is plain Markdown + a little Python, so it plugs into whatever you already use. **Nothing here is bundled** — a public kit can't ship your accounts or credentials. These are the how-tos so you're not lost.

## Obsidian — free, already done

Your `memory/` folder is plain Markdown, which means it *is* an Obsidian vault already. Open the folder in Obsidian and you get backlinks, graph view, and search across your memory + Defect Ledger. The `[[wikilinks]]` between memory files just work. Nothing to configure.

## A second durable surface (Law 6: wrap to ≥2 places)

The wrap protocol says never let one surface be your only memory. The zero-infra default: **git + your files.** Commit your `memory/` folder — now you have local files *and* version history (two surfaces, recoverable). That's enough to start; add a retrieval index only when search gets slow.

## Vector / semantic search (optional — Layer 4)

When grep over your memory stops being enough, add semantic search:

- **[claude-mem](https://github.com/thedotmack/claude-mem)** — auto-captures + re-injects context; the closest turnkey option.
- **Chroma** (or any vector DB) — embed your memory files, query by meaning, and point your wrap step at it as the "retrieval index" surface.

Keep the Markdown files as the **source of truth**; the vector store is an index *over* them, not a replacement.

## Notion / Linear / a structured board (optional)

If you run ops in Notion, add it as a *third* wrap surface — a status page you update at session end. Wire it via the Notion API or an MCP server. This is personal infrastructure; andon leaves a slot for it (the wrap protocol's "optional third: structured ops board") but doesn't ship it.

## The rule for all of these

**Files first.** Integrations are indexes and mirrors *over* your Markdown, never the source of truth. If an integration breaks, your system still works.
