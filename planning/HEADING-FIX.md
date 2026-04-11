# Handoff: Fix Section Headings Rendering as Plain Text

## Why This Exists

A bug was discovered during the Angela Kim Couture pipeline run. This file contains everything needed to understand the problem and implement the fix.

---

## Bug: Section Headings Render as Plain Text

### What happened

In the `01_tools_audit.md` output, section headings appear as bare text without `#` markdown markers:

```
Your Current Tool Stack       <-- should be "## Your Current Tool Stack"
What to Automate              <-- should be "## What to Automate"
Your #1 AI Opportunity        <-- should be "## Your #1 AI Opportunity"
```

This causes them to render as normal paragraphs in all three output formats:
- **DOCX**: The `_convert_markdown_to_docx()` method at line 481 checks `re.match(r'^(#{1,6})\s+(.+)$', stripped)` — without `#`, lines fall through to the paragraph handler
- **PDF**: Same issue in `_convert_markdown()` at line 607 with `re.match(r'^(#{2,6})\s+(.+)$', stripped)`
- **Web UI**: Python's `markdown.markdown()` requires `#` to produce `<h2>`/`<h3>` tags; without them it outputs `<p>` tags. The CSS at `.markdown-content h2`/`h3` (webapp.py lines 562-564) is correct but never applies

### Root cause

Inconsistent Gemini compliance. The system instruction in `generate_markdown()` says "Use proper heading hierarchy" but Gemini doesn't always follow it. Some deliverables get proper headings (02, 03, 05, 06, 07 all used `##`/`###`), but 01_tools_audit did not.

### Which deliverables were affected

Only `01_tools_audit` had plain-text headings in this run. The others all used proper `#` markers. But this is non-deterministic — different runs could affect different deliverables.

### The current system instruction (gemini_client.py ~line 282)

```python
markdown_instruction = """
You are generating professional consulting documentation in Markdown format.
Follow these formatting guidelines:
- Use proper heading hierarchy (# for title, ## for sections, ### for subsections)
- Use bullet points and numbered lists for clarity
- Include tables where appropriate using markdown syntax
- CRITICAL: For markdown tables, each row must be on a single line. Table separator row must only have dashes like |---|---|---|
- Use **bold** for emphasis and `code` for technical terms
- Keep paragraphs concise and actionable
- Do not include ```markdown``` code fences around the output
"""
```

The first bullet is too abstract. Gemini ignores it for some deliverables.

---

## Architecture Context

### Pipeline flow

```
main.py / server.py
  -> research/orchestrator.py (Perplexity queries)
  -> synthesis/orchestrator.py (generates all 8 deliverables)
       -> synthesis/gemini_client.py (API calls with retry)
       -> synthesis/context_builder.py (builds prompts with research)
       -> synthesis/prompts/*.py (8 prompt templates)
  -> generation/orchestrator.py
       -> generation/markdown_generator.py (saves .md files)
       -> generation/docx_generator.py (Word document)
       -> generation/pdf_generator.py (PDF document)
```

### Key files for this fix

| File | Role |
|---|---|
| `strategy_factory/synthesis/gemini_client.py` | Wraps Gemini API. `generate_markdown()` at ~line 266 is where the system instruction lives. |
| `strategy_factory/synthesis/prompts/tech_inventory.py` | Prompt for 01_tools_audit. Sections defined with `###` markers at ~lines 12, 37, 49. |
| `strategy_factory/generation/docx_generator.py` | Converts markdown to Word. Heading detection at line 481. |
| `strategy_factory/generation/pdf_generator.py` | Converts markdown to PDF. Heading detection at line 607. |

---

## Implementation Plan

### Fix: Strengthen heading instruction (prompt-only, no post-processing)

**File**: `strategy_factory/synthesis/gemini_client.py`

In the `generate_markdown()` method (~line 282), add a second bullet after the heading hierarchy line. Change:

```python
markdown_instruction = """
You are generating professional consulting documentation in Markdown format.
Follow these formatting guidelines:
- Use proper heading hierarchy (# for title, ## for sections, ### for subsections)
- Use bullet points and numbered lists for clarity
...
```

To:

```python
markdown_instruction = """
You are generating professional consulting documentation in Markdown format.
Follow these formatting guidelines:
- Use proper heading hierarchy (# for title, ## for sections, ### for subsections)
- CRITICAL: Every section heading in your output MUST start with # markers. Never write a section title as plain text.
  Wrong: Your Current Tool Stack
  Right: ## Your Current Tool Stack
- Use bullet points and numbered lists for clarity
...
```

This is one edit in one file. It applies to all 8 deliverables because `generate_markdown()` is the shared entry point. No changes to individual prompt files are needed.

---

## Files to Modify

| File | Change |
|---|---|
| `strategy_factory/synthesis/gemini_client.py` | Add 2 lines to the `markdown_instruction` string in `generate_markdown()` |

---

## Verification

1. **Heading markers**: After a run, open each markdown file in `output/{slug}/markdown/` and verify all section headings start with `#` markers.
2. **DOCX/PDF**: Open the generated documents. Section headings should render styled (bold, colored, larger font) — not as body text.
3. **Web UI**: Run `python -m strategy_factory.webapp`, view the deliverable tabs. Section headings should render with proper heading styling (larger text, bottom borders on h2, etc.).
