# Plan: Deterministic Heading Fix via Regex Post-Processing

## Context

Gemini inconsistently omits `#` markdown markers on section headings (observed in `01_tools_audit`). Without headings, the DOCX/PDF/Web renderers all produce plain paragraphs instead of styled headings. The existing system instruction says "Use proper heading hierarchy" but Gemini doesn't always comply — sometimes getting some headings right and missing others on the same page.

## Approach

Add a regex-based post-processing step in the Gemini client that scans generated content for lines that look like bare headings and prepends `## `. This is deterministic, has zero API cost, and runs on every generation as a safeguard.

## Changes

### File: `strategy_factory/synthesis/gemini_client.py`

**Add `_fix_bare_headings()` method** (after `_fix_malformed_tables`, ~15 lines)

Heuristic for detecting a bare heading line:
- Line is non-empty and short (< 60 chars after stripping)
- Does NOT start with `#`, `|`, `-`, `*`, `>`, backtick, or numbered list marker (`1.`, `2.`, etc.)
- Does NOT end with sentence punctuation (`.`, `,`, `:`, `;`, `!`, `?`)
- Preceded by a blank line (or is the first line of content)
- Followed by a blank line (or is the last line of content)

If all conditions are met, prepend `## ` to the line.

**Call it in `generate_markdown()`** (line 305-306, alongside `_fix_malformed_tables`)

```python
if result.content:
    result.content = self._fix_malformed_tables(result.content)
    result.content = self._fix_bare_headings(result.content)
```

## Verification

1. Unit test with sample content containing bare headings like `"Your Current Tool Stack"` on its own line — verify `## ` is prepended
2. Verify that already-correct headings (`## Your Current Tool Stack`) are NOT double-prefixed
3. Verify that table rows, list items, and normal paragraphs are NOT modified
4. Run the full pipeline on a test company and check `output/*/markdown/01_tools_audit.md`
