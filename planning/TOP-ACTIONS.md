# Plan: Render "Your Top Actions This Month" as Bordered Cards

## Why This Change

The "Your Top Actions This Month" table in the action plan deliverable has 7 columns (`#`, `Action`, `Tool (Price)`, `Time to Set Up`, `Weekly Time Saved`, `What You Get`, `First Step Today`). On a 6.5" printable page width, each column gets ~0.93" — far too narrow for the long text in Action, What You Get, and First Step Today. This causes:

- **Issue #5**: Columns too narrow, rows extremely tall from wrapping
- **Issue #9**: The tall table gets pushed to the next page, leaving the heading orphaned with a large blank gap above

**Solution**: Detect this specific table and render each row as a bordered card using the full page width. This fixes both issues.

## Card Layout

Each action row becomes a bordered card with light blue background:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Empower Claude Max to draft detailed project proposals   │
│    and manage initial client follow-ups.                    │
│                                                             │
│ Tool: Claude Max ($100-200/mo)                              │
│ Setup: 2-4 hours     Saves: 5-10 hrs/week                  │
│                                                             │
│ What you get: Rapid, customized proposals, consistent       │
│ follow-up, freeing your time to focus on design.            │
│                                                             │
│ First step today: Upload 5-10 of your best past proposals   │
│ and consultation notes into Claude Max.                     │
└─────────────────────────────────────────────────────────────┘
```

Background color `#F5F9FC` (pale blue, already used for alternating table rows elsewhere). Thin gray border (`#CCCCCC`). Full page width. Small gap between cards.

## Detection Strategy

Add a method `_is_action_table(raw_headers) -> bool` to both generators:
- Returns `True` when `len(raw_headers) == 7` AND `raw_headers[0].strip() == "#"`
- No other table in any deliverable has 7 columns (the investment table is 4 columns, readiness/audit tables are also narrower)
- When detected, route to card rendering; all other tables render normally as before

## What NOT to Change

- **`strategy_factory/synthesis/prompts/quick_wins.py`** — the prompt template stays unchanged. The markdown table is the intermediate format that the model generates. Only the rendering layer changes.
- **`_add_table()`** in docx_generator and **`_build_table()`** in pdf_generator — normal table rendering stays untouched.
- No other deliverable generators or orchestrators.

---

## Implementation: DOCX Generator

**File**: `strategy_factory/generation/docx_generator.py`

### 1. Add `_is_action_table` method

Add as a static method near `_clean_table_cell` (around line 629):

```python
@staticmethod
def _is_action_table(raw_headers: List[str]) -> bool:
    """Return True if this is the 7-column action plan table."""
    return len(raw_headers) == 7 and raw_headers[0].strip() == "#"
```

### 2. Add `_add_action_cards` method

Add as a new method on the `DocxGenerator` class. For each row, create a single-cell `Table Grid` table as the card:

```python
def _add_action_cards(self, doc: Document, headers: List[str], rows: List[List[str]]) -> None:
    """Render 7-column action table rows as bordered cards."""
    for row_data in rows:
        # row_data indices: 0=#  1=Action  2=Tool(Price)  3=Time to Set Up
        #                   4=Weekly Time Saved  5=What You Get  6=First Step Today

        card = doc.add_table(rows=1, cols=1)
        card.style = 'Table Grid'
        card.alignment = WD_TABLE_ALIGNMENT.CENTER

        cell = card.rows[0].cells[0]

        # Background shading via OXML (OxmlElement and qn already imported)
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), 'F5F9FC')
        shading.set(qn('w:val'), 'clear')
        cell._tc.get_or_add_tcPr().append(shading)

        # Clear default paragraph
        cell.paragraphs[0].clear()

        # Title: "1. Action text"
        title_para = cell.paragraphs[0]
        title_run = title_para.add_run(f"{row_data[0]}. {row_data[1]}")
        title_run.bold = True
        title_run.font.size = Pt(11)
        title_run.font.color.rgb = RGBColor(31, 78, 121)  # DARK_BLUE
        title_para.paragraph_format.space_after = Pt(6)

        # Tool line
        tool_para = cell.add_paragraph()
        label_run = tool_para.add_run("Tool: ")
        label_run.bold = True
        label_run.font.size = Pt(10)
        label_run.font.color.rgb = RGBColor(64, 64, 64)
        value_run = tool_para.add_run(row_data[2])
        value_run.font.size = Pt(10)
        value_run.font.color.rgb = RGBColor(64, 64, 64)
        tool_para.paragraph_format.space_before = Pt(4)
        tool_para.paragraph_format.space_after = Pt(2)

        # Setup + Saves line (both on one line)
        detail_para = cell.add_paragraph()
        setup_label = detail_para.add_run("Setup: ")
        setup_label.bold = True
        setup_label.font.size = Pt(10)
        setup_label.font.color.rgb = RGBColor(64, 64, 64)
        setup_val = detail_para.add_run(row_data[3])
        setup_val.font.size = Pt(10)
        setup_val.font.color.rgb = RGBColor(64, 64, 64)
        sep = detail_para.add_run("     ")
        sep.font.size = Pt(10)
        saves_label = detail_para.add_run("Saves: ")
        saves_label.bold = True
        saves_label.font.size = Pt(10)
        saves_label.font.color.rgb = RGBColor(64, 64, 64)
        saves_val = detail_para.add_run(row_data[4])
        saves_val.font.size = Pt(10)
        saves_val.font.color.rgb = RGBColor(64, 64, 64)
        detail_para.paragraph_format.space_before = Pt(2)
        detail_para.paragraph_format.space_after = Pt(6)

        # What you get
        get_para = cell.add_paragraph()
        get_label = get_para.add_run("What you get: ")
        get_label.bold = True
        get_label.font.size = Pt(10)
        get_label.font.color.rgb = RGBColor(64, 64, 64)
        get_val = get_para.add_run(row_data[5])
        get_val.font.size = Pt(10)
        get_val.font.color.rgb = RGBColor(64, 64, 64)
        get_para.paragraph_format.space_before = Pt(2)
        get_para.paragraph_format.space_after = Pt(4)

        # First step today
        step_para = cell.add_paragraph()
        step_label = step_para.add_run("First step today: ")
        step_label.bold = True
        step_label.font.size = Pt(10)
        step_label.font.color.rgb = RGBColor(64, 64, 64)
        step_val = step_para.add_run(row_data[6])
        step_val.font.size = Pt(10)
        step_val.font.color.rgb = RGBColor(64, 64, 64)
        step_para.paragraph_format.space_before = Pt(2)
        step_para.paragraph_format.space_after = Pt(4)

        # Gap between cards
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(0)
        spacer.paragraph_format.space_after = Pt(6)
```

**Note on imports**: `WD_TABLE_ALIGNMENT` needs to be imported from `docx.enum.table`. Check if it's already imported; if not, add it to the existing import block at the top of the file.

### 3. Modify `_process_markdown_table` routing

At line 613, change:

```python
# CURRENT:
if headers and rows:
    self._add_table(doc, headers, rows)

# CHANGE TO:
if headers and rows:
    if self._is_action_table(raw_headers):
        self._add_action_cards(doc, headers, rows)
    else:
        self._add_table(doc, headers, rows)
```

`raw_headers` is already computed at line 575 and in scope. Using it (rather than the cleaned `headers`) is safer for detection since `"#"` survives cleaning unchanged.

---

## Implementation: PDF Generator

**File**: `strategy_factory/generation/pdf_generator.py`

### 1. Add color constants

Near existing color constants (lines 38-43), add:

```python
CARD_BG = colors.HexColor("#F5F9FC")
CARD_BORDER = colors.HexColor("#CCCCCC")
```

`CARD_BG` uses the same value as the existing `TABLE_ALT_BG` for visual consistency.

### 2. Add `_is_action_table` method

Same logic as DOCX:

```python
@staticmethod
def _is_action_table(raw_headers: List[str]) -> bool:
    """Return True if this is the 7-column action plan table."""
    return len(raw_headers) == 7 and raw_headers[0].strip() == "#"
```

### 3. Add `_build_action_cards` method

Returns a list of ReportLab flowables (one card per action row):

```python
def _build_action_cards(self, table_lines: List[str]) -> list:
    """Build bordered card flowables from a 7-column action table."""
    raw_headers = [c.strip() for c in table_lines[0].strip("|").split("|")]

    rows = []
    for line in table_lines[2:]:
        if re.match(r"^[\|\s:\-]+$", line):
            continue
        if line.count("-") > 100:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 7:
            continue
        if any(len(c) > 2000 for c in cells):
            continue
        clean_cells = [self._clean_table_cell(c, 500) for c in cells]
        rows.append(clean_cells)

    if not rows:
        return []

    flowables = []
    card_width = 6.5 * inch

    # Styles
    card_title_style = ParagraphStyle(
        "CardTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=DARK_BLUE,
        spaceBefore=0,
        spaceAfter=4,
        leading=15,
    )
    card_detail_style = ParagraphStyle(
        "CardDetail",
        fontName="Helvetica",
        fontSize=10,
        textColor=BODY_GRAY,
        spaceBefore=2,
        spaceAfter=4,
        leading=14,
    )

    for row_data in rows:
        number = self._prep(row_data[0])
        action = self._prep(row_data[1])
        tool = self._prep(row_data[2])
        setup = self._prep(row_data[3])
        saves = self._prep(row_data[4])
        what_get = self._prep(row_data[5])
        first_step = self._prep(row_data[6])

        # 5-row, 1-column table = one card
        card_data = [
            [Paragraph(f"{number}. {action}", card_title_style)],
            [Paragraph(f"<b>Tool:</b> {tool}", card_detail_style)],
            [Paragraph(f"<b>Setup:</b> {setup}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Saves:</b> {saves}", card_detail_style)],
            [Paragraph(f"<b>What you get:</b> {what_get}", card_detail_style)],
            [Paragraph(f"<b>First step today:</b> {first_step}", card_detail_style)],
        ]

        card = Table(card_data, colWidths=[card_width])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.75, CARD_BORDER),
            ("LINEBELOW", (0, 0), (0, 0), 0.5, CARD_BORDER),  # separator after title
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (0, 0), 8),
            ("BOTTOMPADDING", (-1, -1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (0, -2), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        flowables.append(Spacer(1, _GAP_BEFORE_TABLE))
        flowables.append(card)
        flowables.append(Spacer(1, 12))  # 12pt gap between cards

    return flowables
```

**Key design choice**: A 5-row, 1-column `Table` per card rather than multiple Paragraphs in a single cell. This gives clean spacing control via `TOPPADDING`/`BOTTOMPADDING` per row and makes the title separator line straightforward with `LINEBELOW`. The outer `BOX` draws the card border. No `GRID` or `INNERGRID` means the card looks like a unified block.

**Note**: `_prep` is the PDF generator's existing HTML-safe text escaping method. `_clean_table_cell` is the existing cell cleaning method. `ParagraphStyle`, `Table`, `TableStyle`, `Spacer` should all already be imported from reportlab.

### 4. Modify `_flush_table` routing

At ~line 656, change:

```python
# CURRENT:
def _flush_table(self, flowables: list, table_lines: List[str]) -> None:
    """Build a table from accumulated lines and append it with spacing."""
    tbl = self._build_table(table_lines)
    if tbl:
        flowables.append(Spacer(1, _GAP_BEFORE_TABLE))
        flowables.append(tbl)
        flowables.append(Spacer(1, _GAP_AFTER_TABLE))

# CHANGE TO:
def _flush_table(self, flowables: list, table_lines: List[str]) -> None:
    """Build a table (or action cards) from accumulated lines and append with spacing."""
    raw_headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
    if self._is_action_table(raw_headers):
        card_flowables = self._build_action_cards(table_lines)
        flowables.extend(card_flowables)
        return

    tbl = self._build_table(table_lines)
    if tbl:
        flowables.append(Spacer(1, _GAP_BEFORE_TABLE))
        flowables.append(tbl)
        flowables.append(Spacer(1, _GAP_AFTER_TABLE))
```

The early-return pattern avoids modifying `_build_table` at all.

---

## Style Reference

| Element | DOCX | PDF |
|---|---|---|
| Card background | `#F5F9FC` via `w:shd` OXML | `CARD_BG = HexColor("#F5F9FC")` |
| Card border | `Table Grid` style (default thin border) | `BOX` command, 0.75pt, `#CCCCCC` |
| Title | Bold, 11pt, `RGBColor(31,78,121)` | `Helvetica-Bold`, 11pt, `DARK_BLUE` |
| Body text | Regular, 10pt, `RGBColor(64,64,64)` | `Helvetica`, 10pt, `BODY_GRAY` |
| Labels (Tool:, Setup:, etc.) | Bold, 10pt, `RGBColor(64,64,64)` | `<b>` tags within 10pt body |
| Card padding | 4-8pt paragraph spacing | 10pt left/right, 8pt top/bottom |
| Gap between cards | ~12pt spacer paragraph | `Spacer(1, 12)` |

---

## Verification

1. Run the pipeline: `python -m strategy_factory.main resume "Healing Roots Design"` (or use `--skip-research` if research data already exists)
2. Open the generated `.docx` in Word — confirm:
   - 4 action cards appear with borders, full-width text, light blue backgrounds
   - Title line is bold dark blue, body text is gray
   - Setup and Saves share one line
   - Cards have spacing between them
3. Open the generated `.pdf` — confirm same card layout
4. Confirm the "Total Monthly Investment" table (4 columns: Tool/Cost/Does/Paying) still renders as a normal table
5. Confirm the blank-space gap before the action section is gone (issue #9)
