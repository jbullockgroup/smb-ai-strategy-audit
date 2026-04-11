# PDF-FIX: Plan to Fix PDF Issues (REPORT-3, Items 1-3)

## Context

REPORT-3 identifies 3 PDF formatting bugs. All fixes are in a single file: `strategy_factory/generation/pdf_generator.py`.

Source report: `/Users/jeff/ai-strategy-factory/REPORT-3.md`

---

## Fix 1: TOC Missing "Putting It All Together"

**Problem:** The PDF Table of Contents shows 7 sections but omits "Putting It All Together" (the 8th section). The section content renders fine — it's just missing from the TOC.

**Root cause:** `_TOC_SECTION_NUMS` dict at lines 90-98 maps 7 sections to numbers but does not include "Putting It All Together". The `afterFlowable` method (lines 126-137) only creates a TOC entry when `num is not None`, so the 8th section silently drops out.

**Current code (lines 90-98):**
```python
_TOC_SECTION_NUMS = {
    "Executive Summary": 1,
    "Where You Stand Today": 2,
    "Where You're Losing Money": 3,
    "Your AI Readiness": 4,
    "What To Do First": 5,
    "Your Week-by-Week Plan": 6,
    "What It Costs & What You Save": 7,
}
```

**Change:** Add one entry:
```python
_TOC_SECTION_NUMS = {
    "Executive Summary": 1,
    "Where You Stand Today": 2,
    "Where You're Losing Money": 3,
    "Your AI Readiness": 4,
    "What To Do First": 5,
    "Your Week-by-Week Plan": 6,
    "What It Costs & What You Save": 7,
    "Putting It All Together": 8,
}
```

---

## Fix 2: Line Breaks Around Tables and Cards

**Problem:** Tables and cards need more breathing room — the report asks for line breaks before AND after both.

**Current state:**
- Regular tables already have `Spacer(1, _GAP_BEFORE_TABLE)` before and `Spacer(1, _GAP_AFTER_TABLE)` after (lines 683-685 in `_flush_table`).
- Action cards already have `Spacer(1, _GAP_BEFORE_TABLE)` before and `Spacer(1, 12)` after (lines 766-768 in `_build_action_cards`).
- The gap constants are defined at lines 51-55.

**Current constants (lines 51-55):**
```python
_GAP_AFTER_H1 = 10
_GAP_AFTER_H2 = 8
_GAP_AFTER_H3 = 6
_GAP_BEFORE_TABLE = 8
_GAP_AFTER_TABLE = 12
```

**Change:** Increase both table gap constants for more visible spacing:
```python
_GAP_AFTER_H1 = 10
_GAP_AFTER_H2 = 8
_GAP_AFTER_H3 = 6
_GAP_BEFORE_TABLE = 12
_GAP_AFTER_TABLE = 14
```

This also increases the spacing around action cards since `_build_action_cards` (line 766) uses `_GAP_BEFORE_TABLE` for the pre-card spacer. Update the after-card spacer on line 768 to match:

```python
# Before:
flowables.append(Spacer(1, 12))

# After:
flowables.append(Spacer(1, _GAP_AFTER_TABLE))
```

---

## Fix 3: Missing Headings

**Problem:** Markdown headings that appear in the DocX are not rendering in the PDF. The deliverable markdown files use `#` (H1) headings extensively in the body, but the PDF silently skips all of them.

**Root cause:** `_convert_markdown()` at lines 601-604 skips all `#` headings:
```python
# Level-1 headings — skipped per DOCX-STYLING.md (added explicitly by caller)
if re.match(r"^#\s+", stripped):
    i += 1
    continue
```

This was originally intentional because the top-level section headings are added explicitly by the caller via `_h1()`. But the Gemini-generated deliverable content also uses `#` for sub-section headings within each deliverable body. Confirmed examples from actual output:

- `05_readiness_assessment.md`: 4 H1 headings — `# Where You Stand`, `# Your Readiness Scorecard`, `# What Your Score Means`, `# Bottom Line`
- `03_action_plan.md`: 4 H1 headings — `# Your Biggest Opportunity Right Now`, `# Your Top Actions This Month`, `# Tool Recommendations`, `# Total Monthly Investment`
- `04_simple_roadmap.md`: 4 H1 headings — `# Your First 30 Days`, `# Month 2: Build on What's Working`, `# Month 3 and Beyond`, `# Your Weekly Check-In`

All of these are silently dropped in the PDF.

**Change (lines 601-604):** Render body H1 headings as H2 instead of skipping:

```python
# Level-1 headings in deliverable body → render as H2
h1_match = re.match(r"^#\s+(.+)$", stripped)
if h1_match:
    text = self._clean_text(h1_match.group(1))
    flowables.append(Paragraph(self._prep(text), self.styles["h2"]))
    flowables.append(Spacer(1, _GAP_AFTER_H2))
    prev_was_bullet = False
    i += 1
    continue
```

---

## Verification

1. Run a full pipeline (or resume with `--skip-research` if synthesis data exists):
   ```bash
   python -m strategy_factory.main run "Test Company" --skip-research
   ```
   Or test against existing data if a previous run exists:
   ```bash
   python -m strategy_factory.main resume "Angela Kim Couture"
   ```

2. Open the generated PDF and verify:
   - TOC shows all 8 sections including "Putting It All Together" with section number 8
   - Tables and action cards have visible breathing room above and below
   - All headings that appear in the DocX also appear in the PDF (no silently dropped `#` headings)

3. Side-by-side compare PDF with DocX to confirm heading parity
