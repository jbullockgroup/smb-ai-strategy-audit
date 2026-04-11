# PPTX Executive Deck Rebuild — Implementation Handoff

## Why This Change

The current PowerPoint executive deck has 10 slides with hardcoded enterprise content (governance frameworks, Centers of Excellence, generic ROI figures). It doesn't reflect the actual deliverable content that the DOCX and PDF outputs contain. The synthesis prompts have been updated with consistent H3 section headers, so we can now extract targeted content from each deliverable and use Gemini to distill it into slide-appropriate format.

**Goal**: A 10-slide file (1 title + 8 content + 1 thank you) that mirrors the DOCX/PDF deliverables 1:1, pulling the most relevant content from specific H3 sections using a single batch Gemini call.

---

## File to Modify

**`strategy_factory/generation/pptx_generator.py`** — All changes are in this file.

No changes needed to `strategy_factory/synthesis/gemini_client.py` — reuse its existing `generate()` method (lines 94-186).

---

## Architecture Overview

### Current State
- `generate_executive_summary()` (line 56) builds 10 slides, most with hardcoded or generic content
- `_extract_content_section()` (line 447) can target sections by name but its regex only matches `##` (H2), not `###` (H3)
- `_extract_bullets_from_content()` (line 470) only finds markdown bullet markers (`-`, `*`, `+`), can't distill prose into bullets
- `_extract_table_from_content()` (line 480) works fine for parsing markdown tables
- Slide methods like `_add_roi_slide` and `_add_next_steps_slide` use fallback hardcoded data

### Target State
- 10 slides: title → 8 deliverable-aligned content slides → thank you
- Content slides pull from specific H3 sections in the synthesis output
- Gemini distills prose into bullets and abbreviates tables where needed
- A single batch Gemini call produces all 8 content slides at once
- Markdown is stripped before any text enters a slide

---

## Implementation Steps

### Step 1: Fix `_extract_content_section` regex

**Line 463** — The regex only matches `##` headings:

```python
# Current
pattern = rf'##\s*{re.escape(section_name)}.*?\n(.*?)(?=\n##|\Z)'

# Change to
pattern = rf'##+\s*{re.escape(section_name)}.*?\n(.*?)(?=\n##|\Z)'
```

`##` → `##+` lets us target both H2 (`##`) and H3 (`###`) sections. The synthesis prompts use `###` for all sub-sections.

### Step 2: Add `_strip_markdown()` helper

Add as a `@staticmethod` after `_extract_table_from_content` (~line 508).

```python
@staticmethod
def _strip_markdown(text: str) -> str:
    """Remove markdown formatting from text before inserting into slides."""
    # Bold/italic markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Headings
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Links → keep text only
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # Backticks
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
```

Apply in `_add_bullets_to_slide` (line 366) and `_add_table_to_slide` (line 393): strip markdown on each text element before setting it.

### Step 3: Add `_extract_slide_content_via_gemini()` method

This is the core new method. It:
1. Receives `SynthesisOutput`
2. Extracts the relevant H3 sections for all 8 content slides using `_extract_content_section`
3. Sends a single structured prompt to `GeminiClient.generate()` with all sections and per-slide instructions
4. Parses the response into a dict mapping slide number to either a bullet list or a parsed table
5. Returns the dict for the slide-building loop to consume

#### Import needed at top of file:
```python
from ..synthesis.gemini_client import GeminiClient
```

#### Gemini call structure

Single batch call. The response uses `---SLIDE N---` markers. For table slides, the response contains a markdown table. For bullet slides, it contains bullet lines.

Parsing logic: split response by `---SLIDE N---` markers. For each section, check if content starts with `|` (table) → parse via `_extract_table_from_content`. Otherwise → split into bullet lines.

#### The Gemini prompt (build dynamically from synthesis content):

```
You are creating content for a 9-slide executive PowerPoint presentation for a business owner.
Each slide should contain either bullet points or a table. Follow the exact format below.

Output each slide starting with ---SLIDE N--- on its own line, followed by the content.

---SLIDE 1---
[Bullet slides: output 4-5 bullet points, one per line, starting with - ]
These bullets distill the key insights from: {executive summary H3 sections}

---SLIDE 2---
[Table slide: output a markdown table with exactly these columns: Tool, AI Feature Already Built In, What It Could Do For You]
Select the 5-6 most relevant tools from: {tool stack table from 01_tools_audit}
Drop the "What You Use It For" column.

---SLIDE 3---
[Table slide: output the markdown table with columns: Task, Hours/Week Lost, Dollar Value/Week]
Copy from: {time-wasters table from 02_daily_pain_points}
Drop the "Rank" column. Keep all 5 rows.

---SLIDE 4---
[Table slide: output a markdown table with columns: Action, Tool (Price), What You Get]
Pick the top 3 highest-impact actions from: {action plan table from 03_action_plan}

---SLIDE 5---
[Bullet slide: 4-5 key milestones]
Distill from: {roadmap H3 sections from 04_simple_roadmap}

---SLIDE 6---
[Table slide: output the exact table]
Copy exactly from: {readiness scorecard table from 05_readiness_assessment}

---SLIDE 7---
[Bullet slide: 4-5 bullets with real dollar amounts and timeframes]
Distill from these sections ONLY (do NOT include the monthly investment table):
{When You Break Even + The Real Calculation from 06_roi_snapshot}

---SLIDE 8---
[Bullet slide: 4-5 bullets]
Distill from: {closing H3 sections from 07_closing}

Rules:
- Bullets: concise, start with a verb or key fact, no sub-bullets
- Tables: use proper markdown table format with | separators
- No markdown formatting (**, *, ##) in output — plain text only
- Be specific: use real numbers, tool names, dollar amounts from the source content
```

#### Return type

Use a simple dataclass or dict structure:

```python
# For bullet slides: {"type": "bullets", "items": ["bullet1", "bullet2", ...]}
# For table slides: {"type": "table", "headers": [...], "rows": [[...], ...]}
```

### Step 4: Rewrite `generate_executive_summary()`

Replace lines 56-118. New flow:

```python
def generate_executive_summary(self, company_slug, company_input, research, synthesis, mermaid_images=None):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 1. Title slide (unchanged)
    self._add_title_slide(prs, company_input.name, "AI Strategy & Implementation Roadmap",
                          f"Executive Summary | {datetime.now().strftime('%B %Y')}",
                          logo_path=company_input.logo_path)

    # 2. Extract all slide content via single Gemini call
    slide_content = self._extract_slide_content_via_gemini(synthesis)

    # 3. Build 8 content slides from extracted data
    slide_specs = [
        ("Executive Summary", None),
        ("Where You Stand Today", "Your current tools and hidden opportunities"),
        ("Where You're Losing Money", "Your biggest time-wasters ranked"),
        ("What To Do First", "Your top 3 actions this month"),
        ("Your Week-by-Week Plan", "First 30 days and beyond"),
        ("Your AI Readiness", "Your readiness scorecard"),
        ("What It Costs & What You Save", "The ROI of acting now"),
        ("Putting It All Together", "What this all means and your next step"),
    ]

    for i, (title, subtitle) in enumerate(slide_specs, start=1):
        slide = self._add_slide_with_title(prs, title, subtitle)
        content = slide_content.get(i)
        if content:
            if content["type"] == "bullets":
                self._add_bullets_to_slide(slide, content["items"])
            elif content["type"] == "table":
                self._add_table_to_slide(slide, content["headers"], content["rows"])

    # 4. Thank you slide (unchanged)
    self._add_contact_slide(prs)

    # 5. Save
    output_path = self._get_output_path(company_slug, "executive_summary.pptx")
    prs.save(output_path)
    return str(output_path)
```

### Step 5: Delete unused executive summary slide methods

Remove these methods (they're replaced by the generic loop above):
- `_add_executive_summary_slide` (line 514)
- `_add_current_state_slide` (line 535)
- `_add_maturity_slide` (line 565)
- `_add_pain_points_slide` (line 583)
- `_add_quick_wins_slide` (line 601)
- `_add_roadmap_overview_slide` (line 619)
- `_add_roi_slide` (line 637)
- `_add_next_steps_slide` (line 663)

**Keep unchanged**: `_add_title_slide`, `_add_contact_slide`, `_add_slide_with_title`, `_add_bullets_to_slide`, `_add_table_to_slide`, `_add_section_divider`, all `_add_*` methods used by `generate_full_findings`.

### Step 6: Full Findings deck — skip for now

The full findings deck (`generate_full_findings`, line 120) has similar issues but is 30+ slides. The regex fix (Step 1) and markdown stripping (Step 2) will benefit it automatically. A full rewrite is a separate task. Only update the executive deck structure.

---

## Slide-by-Slide Content Map

This is the definitive reference for which H3 sections feed into each slide.

### Slide 1 — Executive Summary → Bullets
- **Deliverable**: `08_executive_summary`
- **H3 sections**: `1. The Big Picture`, `2. What To Do This Week`, `3. The Bottom Line`
- **All prose** — Gemini distills into 4-5 bullets

### Slide 2 — Where You Stand Today → Abbreviated Table
- **Deliverable**: `01_tools_audit`
- **H3 section**: `Your Current Tool Stack`
- **Original table**: 4 columns × 9 rows (Tool, What You Use It For, AI Feature Already Built In, What It Could Do For You)
- **Slide table**: 3 columns × 5-6 rows
  - Keep: `Tool`, `AI Feature Already Built In`, `What It Could Do For You`
  - Drop: `What You Use It For`
  - Gemini selects the 5-6 most relevant tools from the 9

### Slide 3 — Where You're Losing Money → Table
- **Deliverable**: `02_daily_pain_points`
- **H3 section**: `Your Time-Wasters Ranked`
- **Original table**: 4 columns × 5 rows (Rank, Task, Hours/Week Lost, Dollar Value/Week)
- **Slide table**: 3 columns × 5 rows
  - Keep: `Task`, `Hours/Week Lost`, `Dollar Value/Week`
  - Drop: `Rank`

### Slide 4 — What To Do First → Abbreviated Table
- **Deliverable**: `03_action_plan`
- **H3 section**: `Your Top Actions This Month`
- **Original table**: 7 columns × 4-5 rows (#, Action, Tool (Price), Time to Set Up, Weekly Time Saved, What You Get, First Step Today)
- **Slide table**: 3 columns × 3 rows (top 3 actions only)
  - Keep: `Action`, `Tool (Price)`, `What You Get`

### Slide 5 — Your Week-by-Week Plan → Bullets
- **Deliverable**: `04_simple_roadmap`
- **H3 sections**: `Your First 30 Days`, `Month 2: Build on What's Working`, `Month 3 and Beyond`
- **All prose** — Gemini distills into 4-5 key milestones

### Slide 6 — Your AI Readiness → Table (exact copy)
- **Deliverable**: `05_readiness_assessment`
- **H3 section**: `Your Readiness Scorecard`
- **Original table**: 3 columns × 5 rows + total row (Dimension, Score (1-5), Explanation)
- **Slide table**: Exact copy, no changes

### Slide 7 — What It Costs & What You Save → Bullets (NO table)
- **Deliverable**: `06_roi_snapshot`
- **H3 sections**: `When You Break Even`, `The Real Calculation`
- **Important**: Do NOT pull from `Your Monthly Investment` — that table is excluded
- **All prose** — Gemini distills into 4-5 bullets with real dollar amounts and break-even timeline

### Slide 8 — Putting It All Together → Bullets
- **Deliverable**: `07_closing`
- **H3 sections**: `What This All Means`, `Your One Next Step`, `Closing Thought`
- **All prose** — Gemini distills into 4-5 bullets

---

## Deliverable ID to Prompt File Mapping

For reference when looking up prompt templates:

| Deliverable ID | Prompt File | Deliverable Name |
|---|---|---|
| `08_executive_summary` | `synthesis/prompts/executive_summary.py` | Executive Summary |
| `01_tools_audit` | `synthesis/prompts/tech_inventory.py` | Where You Stand Today |
| `02_daily_pain_points` | `synthesis/prompts/pain_points.py` | Where You're Losing Money |
| `03_action_plan` | `synthesis/prompts/quick_wins.py` | What To Do First |
| `04_simple_roadmap` | `synthesis/prompts/roadmap.py` | Your Week-by-Week Plan |
| `05_readiness_assessment` | `synthesis/prompts/maturity_assessment.py` | Your AI Readiness |
| `06_roi_snapshot` | `synthesis/prompts/roi_calculator.py` | What It Costs & What You Save |
| `07_closing` | `synthesis/prompts/closing.py` | Putting It All Together |

---

## Key Existing Code to Reuse

- **`_extract_content_section(synthesis, deliverable_id, section_name)`** — Extracts text under a specific `###` heading (after Step 1 regex fix). Located at line 447.
- **`_extract_table_from_content(content)`** — Parses a markdown table into `{headers: [], rows: [[]]}`. Located at line 480.
- **`GeminiClient.generate(prompt, system_instruction, temperature, max_output_tokens)`** — Makes a Gemini API call with retries and cost tracking. Located in `synthesis/gemini_client.py` line 94.
- **`_add_slide_with_title(prs, title, subtitle)`** — Creates a slide with styled title. Located at line 337.
- **`_add_bullets_to_slide(slide, bullets, ...)`** — Adds bullet list to a slide. Located at line 366.
- **`_add_table_to_slide(slide, headers, rows, ...)`** — Adds a styled table to a slide. Located at line 393.
- **`_add_title_slide(prs, name, title, subtitle, logo_path)`** — Title slide with optional company logo. Located at line 213. Already wired up to use `company_input.logo_path`.
- **`_add_contact_slide(prs)`** — Thank you slide. Located at line 681.

---

## Verification

1. Run the pipeline for a real company (dry-run won't work — skips API calls)
2. Open the generated PPTX and check:
   - 10 slides total (1 title + 8 content + 1 thank you)
   - Company logo on title slide
   - Slides 2, 3, 4, 6 have tables; slides 1, 5, 7, 8 have bullets
   - No raw markdown (`**`, `##`, `*`) visible in any slide
   - No hardcoded enterprise content (governance frameworks, Centers of Excellence, generic ROI figures)
   - ROI slide (7) shows real dollar figures and break-even timeline from the deliverable, not a table
   - Roadmap slide (5) shows actual milestones, not a hardcoded phase table
   - Tool stack table (2) has 3 columns and 5-6 rows (not the full 9)
   - Action plan table (4) has 3 columns and 3 rows (not the full 4-5 × 7)
3. Regression: confirm DOCX and PDF generation still works unchanged
