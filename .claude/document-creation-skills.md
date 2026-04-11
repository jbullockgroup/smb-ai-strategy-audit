# Document Creation Skills Reference

This is my internal reference for creating DOCX, PDF, Excel, and PowerPoint files programmatically.

---

## Setup Requirements

Before creating any documents, ensure a virtual environment with required packages:

```bash
python3 -m venv venv
source venv/bin/activate
pip install python-docx reportlab openpyxl python-pptx
```

---

## 1. DOCX (Word Documents)

### Library: `python-docx`

### Step-by-Step Process

1. **Import required modules**
```python
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
```

2. **Create document instance**
```python
doc = Document()
```

3. **Add title/headings**
```python
# Title (level 0)
title = doc.add_heading('Document Title', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Section headings (levels 1-9)
doc.add_heading('Section Name', level=1)
doc.add_heading('Subsection', level=2)
```

4. **Add paragraphs**
```python
doc.add_paragraph('Regular paragraph text here.')

# With alignment
para = doc.add_paragraph('Centered text')
para.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

5. **Add lists**
```python
# Bullet points
doc.add_paragraph('First item', style='List Bullet')
doc.add_paragraph('Second item', style='List Bullet')

# Numbered list
doc.add_paragraph('Step one', style='List Number')
doc.add_paragraph('Step two', style='List Number')
```

6. **Add tables**
```python
table = doc.add_table(rows=4, cols=3)
table.style = 'Table Grid'

# Populate header row
headers = ['Column A', 'Column B', 'Column C']
for i, header in enumerate(headers):
    table.rows[0].cells[i].text = header

# Populate data rows
for row_idx, row_data in enumerate(data, start=1):
    for col_idx, value in enumerate(row_data):
        table.rows[row_idx].cells[col_idx].text = str(value)
```

7. **Format text runs**
```python
from docx.shared import Pt, RGBColor

paragraph = doc.add_paragraph()
run = paragraph.add_run('Formatted text')
run.bold = True
run.italic = True
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x00, 0x00, 0xFF)
```

8. **Save document**
```python
doc.save('output.docx')
```

### Common Styles
- `'List Bullet'`, `'List Number'`
- `'Table Grid'`
- `'Normal'`, `'Heading 1'`, `'Heading 2'`

---

## 2. PDF Files

### Library: `reportlab`

### Step-by-Step Process (Platypus Method - Recommended)

1. **Import required modules**
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
```

2. **Create document template**
```python
doc = SimpleDocTemplate('output.pdf', pagesize=letter)
styles = getSampleStyleSheet()
story = []  # Container for all elements
```

3. **Add title with custom style**
```python
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    alignment=1,  # 0=left, 1=center, 2=right
    spaceAfter=20
)
story.append(Paragraph('Document Title', title_style))
```

4. **Add headings and paragraphs**
```python
story.append(Paragraph('Section Heading', styles['Heading2']))
story.append(Paragraph('Body text goes here.', styles['Normal']))
```

5. **Add spacing**
```python
story.append(Spacer(1, 0.5 * inch))  # width, height
```

6. **Add tables**
```python
table_data = [
    ['Header 1', 'Header 2', 'Header 3'],
    ['Row 1 Col 1', 'Row 1 Col 2', 'Row 1 Col 3'],
    ['Row 2 Col 1', 'Row 2 Col 2', 'Row 2 Col 3']
]

table = Table(table_data, colWidths=[2*inch, 2*inch, 1.5*inch])
table.setStyle(TableStyle([
    # Header row styling
    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    # Data rows styling
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))
story.append(table)
```

7. **Build the PDF**
```python
doc.build(story)
```

### Available Styles
- `'Normal'`, `'BodyText'`
- `'Heading1'`, `'Heading2'`, `'Heading3'`
- `'Title'`, `'Italic'`, `'Code'`

### Table Style Commands
- `('BACKGROUND', (col1, row1), (col2, row2), color)`
- `('TEXTCOLOR', ...)`
- `('ALIGN', ...)` - 'LEFT', 'CENTER', 'RIGHT'
- `('GRID', (0, 0), (-1, -1), linewidth, color)`
- `('FONTNAME', ...)`, `('FONTSIZE', ...)`

---

## 3. Excel Spreadsheets (XLSX)

### Library: `openpyxl`

### Step-by-Step Process

1. **Import required modules**
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
```

2. **Create workbook and access sheet**
```python
wb = Workbook()
ws = wb.active
ws.title = "Sheet Name"

# Add additional sheets
ws2 = wb.create_sheet(title="Second Sheet")
```

3. **Write data to cells** (IMPORTANT: 1-based indexing!)
```python
# By cell reference
ws['A1'] = 'Header Text'

# By row/column (1-based!)
ws.cell(row=2, column=1, value='Data Value')
```

4. **Add formulas (NOT hardcoded values)**
```python
# Sum formula
ws['E5'] = '=SUM(B5:D5)'

# Reference formula
ws['C10'] = '=A1*B1'

# Cross-column formula
col_letter = get_column_letter(col)
ws.cell(row=7, column=col).value = f'={col_letter}4-{col_letter}5'
```

5. **Apply styling**
```python
# Font styles
header_font = Font(bold=True, color='FFFFFF', size=12)
input_font = Font(color='0000FF')      # Blue = user inputs
formula_font = Font(color='000000')    # Black = formulas
link_font = Font(color='008000')       # Green = internal links
external_font = Font(color='FF0000')   # Red = external refs

# Background fills
header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
highlight_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')  # Yellow = key assumptions

# Borders
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

# Apply to cell
ws['A1'].font = header_font
ws['A1'].fill = header_fill
ws['A1'].alignment = Alignment(horizontal='center')
ws['A1'].border = thin_border
```

6. **Number formatting**
```python
ws['B1'].number_format = '$#,##0'       # Currency
ws['C1'].number_format = '0.0%'         # Percentage
ws['D1'].number_format = '#,##0'        # Number with commas
ws['E1'].number_format = '@'            # Text (for years)
```

7. **Adjust column widths**
```python
ws.column_dimensions['A'].width = 15
ws.column_dimensions[get_column_letter(2)].width = 12
```

8. **Merge cells**
```python
ws.merge_cells('A1:E1')
```

9. **Save workbook**
```python
wb.save('output.xlsx')
```

### Financial Model Color Convention (CRITICAL)
| Color | Font Code | Usage |
|-------|-----------|-------|
| Blue | `0000FF` | User-adjustable inputs |
| Black | `000000` | Formulas/calculations |
| Green | `008000` | Links to other worksheets |
| Red | `FF0000` | External file references |
| Yellow bg | `FFFF00` | Key assumptions |

### Best Practices
- Always use formulas, never hardcode calculated values
- Put assumptions in separate cells, reference via formulas
- Use 1-based indexing (row 1, column 1 = A1)
- Format years as text, currency with units

---

## 4. PowerPoint Presentations (PPTX)

### Library: `python-pptx`

### Step-by-Step Process

1. **Import required modules**
```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor  # NOTE: RGBColor not RgbColor
from pptx.enum.text import PP_ALIGN
```

2. **Create presentation**
```python
prs = Presentation()
```

3. **Add slides**
```python
# Common layouts:
# 0 = Title Slide
# 1 = Title and Content
# 5 = Title Only
# 6 = Blank (most flexible)

slide_layout = prs.slide_layouts[6]  # Blank
slide = prs.slides.add_slide(slide_layout)
```

4. **Add text boxes**
```python
left = Inches(0.5)
top = Inches(2)
width = Inches(9)
height = Inches(1.5)

textbox = slide.shapes.add_textbox(left, top, width, height)
tf = textbox.text_frame
tf.word_wrap = True

# Access first paragraph
p = tf.paragraphs[0]
p.text = "Title Text"
p.font.size = Pt(44)
p.font.bold = True
p.font.color.rgb = RGBColor(31, 78, 121)  # Dark blue
p.alignment = PP_ALIGN.CENTER
```

5. **Add multiple paragraphs (bullet points)**
```python
textbox = slide.shapes.add_textbox(left, top, width, height)
tf = textbox.text_frame
tf.word_wrap = True

bullets = ["First point", "Second point", "Third point"]

for i, text in enumerate(bullets):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = f"• {text}"
    p.font.size = Pt(20)
    p.space_after = Pt(12)
```

6. **Add tables**
```python
rows, cols = 3, 2
left = Inches(1.5)
top = Inches(2)
width = Inches(7)
height = Inches(2)

table = slide.shapes.add_table(rows, cols, left, top, width, height).table

# Set column widths
table.columns[0].width = Inches(3)
table.columns[1].width = Inches(4)

# Add content
table.cell(0, 0).text = "Header 1"
table.cell(0, 1).text = "Header 2"
table.cell(1, 0).text = "Data 1"
table.cell(1, 1).text = "Data 2"
```

7. **Save presentation**
```python
prs.save('output.pptx')
```

### Design Guidelines
- Use web-safe fonts: Arial, Helvetica, Georgia, Times New Roman
- Ensure strong text contrast (dark text on light, light on dark)
- Maintain consistent styling across slides
- Standard slide: 10" x 7.5"

### Common Colors (RGBColor)
```python
dark_blue = RGBColor(31, 78, 121)   # Professional headers
gray = RGBColor(89, 89, 89)         # Subtitles
black = RGBColor(0, 0, 0)           # Body text
white = RGBColor(255, 255, 255)     # Light text on dark bg
```

---

## Quick Reference Table

| Task | DOCX | PDF | XLSX | PPTX |
|------|------|-----|------|------|
| Create | `Document()` | `SimpleDocTemplate()` | `Workbook()` | `Presentation()` |
| Add text | `add_paragraph()` | `Paragraph()` | `ws['A1'] = text` | `add_textbox()` |
| Add table | `add_table(r,c)` | `Table(data)` | cell references | `add_table(r,c,...)` |
| Style text | `run.font.*` | `ParagraphStyle` | `Font()` | `p.font.*` |
| Save | `.save(path)` | `.build(story)` | `.save(path)` | `.save(path)` |

---

## Common Gotchas

1. **python-pptx**: Import `RGBColor` not `RgbColor`
2. **openpyxl**: Uses 1-based indexing (row=1, column=1 for A1)
3. **reportlab**: Build PDF at end with `doc.build(story)`
4. **All**: Create virtual environment to avoid system Python conflicts
