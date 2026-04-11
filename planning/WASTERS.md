# Plan: Add "Time Wasters & Bottlenecks" headline to Daily Pain Points UI

## Context

REPORT.md issue #6: The DOCX/PDF generator adds a "Time-Wasters & Bottlenecks" subsection title manually at `docx_generator.py:103`, but this heading only exists in the PDF output — it never appears in the raw markdown, so the webapp UI doesn't show it. The user wants this headline visible in the pain points section of the webapp UI.

**User note**: Issue #4 ("What's Still Manual" wording in the prompt template) has already been resolved separately — do not touch that.

## Root Cause

The DOCX generator manually injects a subsection title at line 103:

```python
# docx_generator.py:103
self._add_subsection(doc, synthesis, "02_daily_pain_points", "Time-Wasters & Bottlenecks", 2)
```

This is a DOCX-only wrapper heading. The pain points prompt template (`pain_points.py`) never instructs Gemini to produce this heading, so it doesn't appear in the generated markdown, and therefore doesn't render in the webapp UI.

## Files to Modify

### 1. `strategy_factory/synthesis/prompts/pain_points.py`

**What**: Add an instruction telling Gemini to start its output with a `## Time Wasters & Bottlenecks` heading.

**Where**: After the opening instruction paragraph (line 6: "Based on the company research provided, write a plain-English breakdown...") and before the `## What to produce` section (line 8). Add:

```
Start your output with this heading on its own line:

## Time Wasters & Bottlenecks

Then write the sections below.
```

This makes the generated markdown structure:

```markdown
# Where You're Losing Money          ← from config.py "name" field (added by markdown_generator)
## Time Wasters & Bottlenecks         ← NEW: from prompt instruction
### The 500 Customer Test             ← existing section
### Your Time-Wasters Ranked          ← existing section
### Your Highest-Impact Workflows     ← existing section
### The Content Creation Gap          ← existing section
### What Your Competitors Are Up To   ← existing section
### Your Industry's AI Moment         ← existing section
```

The webapp renders this markdown as HTML, so the new H2 heading will appear in the UI automatically — no webapp code changes needed.

### 2. `strategy_factory/generation/docx_generator.py` (line 103)

**What**: Update the hardcoded subsection title to match the new prompt heading wording exactly, keeping PDF and UI consistent.

**Current** (line 103):
```python
self._add_subsection(doc, synthesis, "02_daily_pain_points", "Time-Wasters & Bottlenecks", 2)
```

**Change to**:
```python
self._add_subsection(doc, synthesis, "02_daily_pain_points", "Time Wasters & Bottlenecks", 2)
```

(Remove the hyphen and ampersand — use plain "and" to match the prompt template heading.)

**Note**: Since the prompt will now generate this heading as part of the markdown content, check whether `_add_subsection_from_deliverable` duplicates it in the PDF. If it parses the markdown and renders the H2, the manual subsection title in `_add_subsection` may create a duplicate. If so, remove the manual `_add_subsection` call and just use `_add_subsection_from_deliverable` directly (like the other deliverables do) — or verify that the DOCX generator handles the already-present H2 gracefully.

## Files NOT to Modify

- `strategy_factory/webapp.py` — No changes needed; the webapp renders markdown as-is
- `strategy_factory/config.py` — No changes needed; deliverable name stays "Where You're Losing Money"
- `strategy_factory/generation/markdown_generator.py` — No changes needed; it adds the H1 title from config
- `strategy_factory/synthesis/prompts/tech_inventory.py` — Already handled separately (issue #4)

## Verification

1. Read the modified prompt template to confirm the heading instruction is in place
2. Read the modified DOCX generator to confirm matching wording
3. Run `python -m strategy_factory.main run "Test Company" --dry-run` to confirm no import/syntax errors
4. Full test: run the pipeline for a company and verify:
   - The generated `02_daily_pain_points.md` starts with `## Time Wasters & Bottlenecks`
   - The webapp UI at `http://localhost:8888` shows the heading when viewing pain points
   - The PDF still renders correctly (check for duplicate headings)
