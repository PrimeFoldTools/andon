---
name: skill-name-kebab-case
description: One sentence describing what this skill does and when to invoke it. The agent uses this to decide whether to route here. Be specific, name trigger phrases.
input_contract: What the caller must provide (e.g., "raw draft text", "JSON spec with X/Y/Z fields", "file path to image")
output_contract: What this skill produces (e.g., "publication-ready markdown", "validated JSON matching schema", "ranked list with reasoning")
composable_role: primitive | router | pipeline
---

# Skill Name

One paragraph: what this skill does, what problem it solves, why it exists.

## When to invoke

- Trigger phrase 1
- Trigger phrase 2
- Specific task type 3

Don't invoke for:

- <what looks similar but isn't this>
- <what belongs to a different skill>

## Core workflow

### Phase 1 — <Phase name>

What happens in this phase. Inputs. Decisions. Outputs.

1. Step
2. Step
3. Step

### Phase 2 — <Phase name>

What happens here. Why it's distinct from phase 1.

1. Step
2. Step

### Phase 3 — <Phase name>

Final phase. Output format. Quality checklist.

## Execution modes

If this skill has fast / full modes, describe them.

- **FAST mode** — when, what, output format
- **FULL mode** — when, what, output format

## Output format

```
<exact output template>
```

## Quality checklist

Before returning, check:

- [ ] <quality criterion 1>
- [ ] <quality criterion 2>
- [ ] <quality criterion 3>

## Common failure modes

- *<failure 1>* — how to avoid
- *<failure 2>* — how to avoid

## Composes with

- <other skill 1> — what it provides as input
- <other skill 2> — what it consumes as output

## Notes

- Keep this skill file under ~2K tokens. Long skills become un-loadable.
- Frontmatter fields are load-bearing — the loader fails on missing `name` or `description`.
- `input_contract` and `output_contract` are how downstream skills decide whether to chain to this one.
