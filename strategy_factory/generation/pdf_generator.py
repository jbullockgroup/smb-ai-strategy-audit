"""
PDF generator for final AI strategy report using ReportLab.

Produces a styled PDF from synthesized deliverables, matching the
brand colors and structure of the Word document output.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from ..config import OUTPUT_DIR
from ..models import CompanyInput, ResearchOutput, SynthesisOutput

# Auditor branding logo for cover page footer
_AUDITOR_LOGO = Path(__file__).resolve().parent.parent.parent / "assets" / "auditor-logo" / "auditor-logo.png"

# Brand colors matching the DOCX output (DOCX-STYLING.md)
DARK_BLUE = colors.HexColor("#1F4E79")
MED_BLUE = colors.HexColor("#4472C4")
BODY_GRAY = colors.HexColor("#404040")
LIGHT_GRAY = colors.HexColor("#808080")
TABLE_HEADER_BG = colors.HexColor("#D6E4F0")
TABLE_ALT_BG = colors.HexColor("#F5F9FC")
CARD_BG = colors.HexColor("#F5F9FC")
CARD_BORDER = colors.HexColor("#CCCCCC")

# Explicit gap constants used throughout the document.
# Using explicit Spacers (rather than relying solely on spaceBefore/spaceAfter)
# because ReportLab suppresses spaceBefore on the first element kept with a
# heading via keepWithNext, which causes the "jammed under heading" appearance.
_GAP_AFTER_H1 = 10       # pts — gap between H1 heading and its first body paragraph
_GAP_AFTER_H2 = 8        # pts — gap between H2 heading and its first body paragraph
_GAP_AFTER_H3 = 6        # pts — gap between H3/H4 heading and content
_GAP_BEFORE_TABLE = 12   # pts — breathing room before a table
_GAP_AFTER_TABLE = 14    # pts — breathing room after a table

# Map of Unicode characters that Helvetica (Latin-1) cannot render → ASCII equivalents.
# Any character outside Latin-1 (codepoint > 255) that isn't in this map will be
# replaced with '?' by _sanitize() as a last resort.
_UNICODE_MAP = {
    "\u2011": "-",    # non-breaking hyphen
    "\u2012": "-",    # figure dash
    "\u2013": "-",    # en dash
    "\u2014": "--",   # em dash
    "\u2015": "--",   # horizontal bar
    "\u2018": "'",    # left single quotation mark
    "\u2019": "'",    # right single quotation mark
    "\u201a": ",",    # single low-9 quotation mark
    "\u201c": '"',    # left double quotation mark
    "\u201d": '"',    # right double quotation mark
    "\u201e": '"',    # double low-9 quotation mark
    # bullet character removed — we render • directly now
    "\u2026": "...",  # horizontal ellipsis
    "\u00a0": " ",    # non-breaking space
    "\u00ad": "-",    # soft hyphen
    "\u2032": "'",    # prime
    "\u2033": '"',    # double prime
    "\u2039": "<",    # single left angle quotation mark
    "\u203a": ">",    # single right angle quotation mark
    "\u20ac": "EUR",  # euro sign (not in Latin-1)
    "\u2122": "(TM)", # trade mark sign
    "\u00ae": "(R)",  # registered sign
    "\u00a9": "(C)",  # copyright sign
}


# Ordered list of top-level sections — used to assign TOC numbers and
# to match H1 paragraph text in afterFlowable so the right page number
# is recorded on each multiBuild pass.
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


class _StrategyDocTemplate(BaseDocTemplate):
    """
    BaseDocTemplate subclass with a single page template and TOC support.

    Overrides afterFlowable to broadcast 'TOCEntry' notifications whenever an
    H1-styled Paragraph is encountered, so that a TableOfContents flowable
    in the story picks up the correct page number on each multiBuild pass.
    """

    def __init__(self, filename: str, on_later_pages, **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        frame = Frame(
            self.leftMargin, self.bottomMargin,
            self.width, self.height,
            id="normal",
        )
        self.addPageTemplates([
            PageTemplate(
                id="All",
                frames=frame,
                onPage=on_later_pages,
                pagesize=self.pagesize,
            )
        ])

    def afterFlowable(self, flowable):
        """Notify the TOC when an H1 heading is laid out."""
        if isinstance(flowable, Paragraph) and flowable.style.name == "PDFH1":
            raw = flowable.getPlainText()
            num = _TOC_SECTION_NUMS.get(raw)
            if num is not None:
                safe = raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                entry = (
                    f'<font color="#1F4E79"><b>{num}.</b></font>'
                    f'&#160;&#160;&#160;{safe}'
                )
                self.notify("TOCEntry", (0, entry, self.page))


class PDFGenerator:
    """
    Generates a PDF version of the final AI strategy report.

    Consumes the same synthesis data as DocxGenerator and produces
    a branded PDF using ReportLab — no external tools required.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.styles = self._build_styles()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate_strategy_report(
        self,
        company_slug: str,
        company_input: CompanyInput,
        research: ResearchOutput,
        synthesis: SynthesisOutput,
    ) -> str:
        """
        Generate final AI strategy report as PDF.

        Returns path to generated PDF file as a string.
        """
        output_path = self._get_output_path(company_slug, "final_strategy_report.pdf")

        # Build the TableOfContents flowable first so the doc template can
        # register it as an IndexingFlowable and populate page numbers via
        # multiBuild (two-pass rendering).
        toc = self._build_toc_flowable()

        doc = _StrategyDocTemplate(
            str(output_path),
            on_later_pages=self._later_pages,
            pagesize=letter,
            leftMargin=inch,
            rightMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        story: List = []

        # Cover page
        story.extend(self._build_cover_page(
            company_input.name,
            "AI Strategy & Implementation Report",
            datetime.now().strftime("%B %Y"),
            logo_path=company_input.logo_path,
        ))

        # Table of contents page
        story.extend(self._build_toc_page(toc))

        # Executive Summary
        story.extend(self._h1("Executive Summary"))
        story.extend(self._build_from_deliverable(synthesis, "08_executive_summary"))

        # Where You Stand Today
        story.extend(self._h1("Where You Stand Today"))
        story.extend(self._build_from_deliverable(synthesis, "01_tools_audit"))

        # Where You're Losing Money
        story.extend(self._h1("Where You're Losing Money"))
        story.extend(self._build_from_deliverable(synthesis, "02_daily_pain_points"))

        # Your AI Readiness
        story.extend(self._h1("Your AI Readiness"))
        story.extend(self._build_from_deliverable(synthesis, "05_readiness_assessment"))

        # What To Do First
        story.extend(self._h1("What To Do First"))
        story.extend(self._build_from_deliverable(synthesis, "03_action_plan"))

        # Your Week-by-Week Plan
        story.extend(self._h1("Your Week-by-Week Plan"))
        story.extend(self._build_from_deliverable(synthesis, "04_simple_roadmap"))

        # What It Costs & What You Save
        story.extend(self._h1("What It Costs & What You Save"))
        story.extend(self._build_from_deliverable(synthesis, "06_roi_snapshot"))

        # Putting It All Together
        story.extend(self._h1("Putting It All Together"))
        story.extend(self._build_from_deliverable(synthesis, "07_closing"))

        doc.multiBuild(story)

        return str(output_path)

    # -------------------------------------------------------------------------
    # Heading helpers — always include an explicit trailing Spacer so content
    # is never jammed directly beneath a heading, regardless of the following
    # element's spaceBefore value.
    # -------------------------------------------------------------------------

    def _h1(self, text: str) -> list:
        return [
            Paragraph(self._prep(text), self.styles["h1"]),
            Spacer(1, _GAP_AFTER_H1),
        ]

    def _h2(self, text: str) -> list:
        return [
            Paragraph(self._prep(text), self.styles["h2"]),
            Spacer(1, _GAP_AFTER_H2),
        ]

    # -------------------------------------------------------------------------
    # Page layout callbacks
    # -------------------------------------------------------------------------

    @staticmethod
    def _first_page(canvas_obj, doc):
        """No footer on the cover page (kept for legacy compatibility)."""
        pass

    @staticmethod
    def _later_pages(canvas_obj, doc):
        """Centered page number in footer; cover page (page 1) is skipped."""
        if canvas_obj.getPageNumber() == 1:
            return
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(LIGHT_GRAY)
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawCentredString(4.25 * inch, 0.5 * inch, f"Page {page_num}")
        canvas_obj.restoreState()

    # -------------------------------------------------------------------------
    # Styles  (per DOCX-STYLING.md)
    # -------------------------------------------------------------------------

    def _build_styles(self) -> dict:
        """Build ReportLab paragraph styles matching the DOCX brand palette."""
        return {
            # Headings — keepWithNext removed; spacing is handled via explicit
            # Spacer flowables appended by _h1()/_h2() so it can't be suppressed.
            "h1": ParagraphStyle(
                "PDFH1",
                fontName="Helvetica-Bold",
                fontSize=18,
                textColor=DARK_BLUE,
                spaceBefore=24,
                spaceAfter=0,   # Spacer added explicitly by _h1()
            ),
            "h2": ParagraphStyle(
                "PDFH2",
                fontName="Helvetica-Bold",
                fontSize=14,
                textColor=MED_BLUE,
                spaceBefore=18,
                spaceAfter=0,   # Spacer added explicitly by _h2()
            ),
            # Headings that appear inside markdown content (no explicit helper)
            # keep their spaceAfter so the converter can add a Spacer after them.
            "h3": ParagraphStyle(
                "PDFH3",
                fontName="Helvetica-Bold",
                fontSize=12,
                textColor=MED_BLUE,
                spaceBefore=12,
                spaceAfter=0,
            ),
            "h4": ParagraphStyle(
                "PDFH4",
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=BODY_GRAY,
                spaceBefore=8,
                spaceAfter=0,
            ),
            "body": ParagraphStyle(
                "PDFBody",
                fontName="Helvetica",
                fontSize=11,
                textColor=BODY_GRAY,
                spaceBefore=8,   # DOCX-STYLING.md: 8pt (max with bullet spaceAfter=3 → 8pt gap)
                spaceAfter=6,
                leading=16,
            ),
            # Bold-only lines like **Key Strengths:** get extra top space
            "body_pseudo_heading": ParagraphStyle(
                "PDFBodyPseudoHeading",
                fontName="Helvetica",
                fontSize=11,
                textColor=BODY_GRAY,
                spaceBefore=12,  # DOCX-STYLING.md: 12pt for pseudo-headings
                spaceAfter=6,
                leading=16,
            ),
            "bullet": ParagraphStyle(
                "PDFBullet",
                fontName="Helvetica",
                fontSize=11,
                textColor=BODY_GRAY,
                spaceBefore=6,
                spaceAfter=4,
                leading=16,
                leftIndent=20,
            ),
            "sub_bullet": ParagraphStyle(
                "PDFSubBullet",
                fontName="Helvetica",
                fontSize=11,
                textColor=BODY_GRAY,
                spaceBefore=4,
                spaceAfter=4,
                leading=16,
                leftIndent=40,
            ),
            "code": ParagraphStyle(
                "PDFCode",
                fontName="Courier",
                fontSize=10,     # DOCX-STYLING.md: 10pt
                textColor=colors.HexColor("#333333"),
                spaceBefore=2,
                spaceAfter=2,
                leading=13,
                leftIndent=24,
                backColor=colors.HexColor("#F5F5F5"),
            ),
            "toc_entry": ParagraphStyle(
                "PDFTocEntry",
                fontName="Helvetica",
                fontSize=11,
                textColor=BODY_GRAY,
                spaceBefore=6,
                spaceAfter=6,
                leftIndent=0,
            ),
            "cover_company": ParagraphStyle(
                "PDFCoverCompany",
                fontName="Helvetica-Bold",
                fontSize=28,
                textColor=DARK_BLUE,
                alignment=TA_CENTER,
                spaceAfter=16,
            ),
            "cover_title": ParagraphStyle(
                "PDFCoverTitle",
                fontName="Helvetica",
                fontSize=24,     # DOCX-STYLING.md: 24pt
                textColor=BODY_GRAY,
                alignment=TA_CENTER,
                spaceAfter=12,
            ),
            "cover_subtitle": ParagraphStyle(
                "PDFCoverSubtitle",
                fontName="Helvetica",
                fontSize=14,
                textColor=LIGHT_GRAY,
                alignment=TA_CENTER,
                spaceAfter=8,
            ),
        }

    # -------------------------------------------------------------------------
    # Page-level builders
    # -------------------------------------------------------------------------

    def _build_cover_page(self, company_name: str, title: str, subtitle: str,
                          logo_path: str = None) -> list:
        """Build cover page flowables."""
        flowables = []

        if logo_path and Path(logo_path).exists():
            from reportlab.platypus import Image as RLImage
            from PIL import Image as PILImage

            img = PILImage.open(logo_path)
            img_w, img_h = img.size
            aspect = img_w / img_h
            max_w = 2.0 * inch
            max_h = 1.5 * inch
            if aspect > (2.0 / 1.5):
                width = max_w
                height = max_w / aspect
            else:
                height = max_h
                width = max_h * aspect

            flowables.append(Spacer(1, 1.0 * inch))
            flowables.append(RLImage(str(logo_path), width=width, height=height,
                                     hAlign='CENTER'))
            flowables.append(Spacer(1, 0.3 * inch))
        else:
            flowables.append(Spacer(1, 2.5 * inch))

        flowables.extend([
            Paragraph(self._prep(company_name), self.styles["cover_company"]),
            Spacer(1, 0.3 * inch),
            Paragraph(self._prep(title), self.styles["cover_title"]),
            Spacer(1, 0.2 * inch),
            Paragraph(self._prep(subtitle), self.styles["cover_subtitle"]),
            Spacer(1, 0.4 * inch),
            HRFlowable(width="80%", thickness=2, color=DARK_BLUE),
        ])

        # Auditor branding footer
        if _AUDITOR_LOGO.exists():
            from reportlab.platypus import Image as RLImage
            from PIL import Image as PILImage

            img = PILImage.open(str(_AUDITOR_LOGO))
            img_w, img_h = img.size
            aspect = img_w / img_h
            target_w = 1.0 * inch
            target_h = target_w / aspect

            footer_style = ParagraphStyle(
                "CoverFooter",
                fontName="Helvetica",
                fontSize=11,
                textColor=LIGHT_GRAY,
                alignment=TA_CENTER,
                leading=15,
            )
            footer_small = ParagraphStyle(
                "CoverFooterSmall",
                parent=footer_style,
                fontSize=10,
            )

            flowables.extend([
                Spacer(1, 0.6 * inch),
                RLImage(str(_AUDITOR_LOGO), width=target_w, height=target_h,
                        hAlign='CENTER'),
                Spacer(1, 0.1 * inch),
                Paragraph("Prepared by Early AIdopters", footer_style),
                Paragraph("https://www.skool.com/earlyaidopters/about", footer_small),
            ])

        flowables.append(PageBreak())
        return flowables

    def _build_toc_flowable(self) -> TableOfContents:
        """
        Create a TableOfContents IndexingFlowable.

        Entries are populated automatically by _StrategyDocTemplate.afterFlowable
        during multiBuild.  The entry text is rich markup so the section number
        renders in DARK_BLUE bold and the title in BODY_GRAY.
        """
        toc = TableOfContents()
        toc.dotsMinLevel = 0   # dot leaders at level 0
        toc.levelStyles = [
            ParagraphStyle(
                "TOCLevel0",
                fontName="Helvetica",
                fontSize=11,
                textColor=BODY_GRAY,
                leading=16,
                spaceBefore=5,
                spaceAfter=5,
            )
        ]
        return toc

    def _build_toc_page(self, toc: TableOfContents) -> list:
        """Wrap the TOC flowable in a titled page with a PageBreak at the end."""
        return [
            Paragraph("Table of Contents", self.styles["h1"]),
            Spacer(1, 22),   # extra breathing room between heading and entries
            toc,
            PageBreak(),
        ]

    # -------------------------------------------------------------------------
    # Section content builders
    # -------------------------------------------------------------------------


    def _build_from_deliverable(self, synthesis: SynthesisOutput, deliverable_id: str) -> list:
        """Convert a synthesis deliverable's markdown content to PDF flowables."""
        deliverable = synthesis.deliverables.get(deliverable_id)
        if not deliverable or not deliverable.content:
            return [Paragraph("[Content not available]", self.styles["body"])]
        # Strip a leading H1 — the generator already added the section heading,
        # and some deliverables start with `# Title` while others don't.
        content = re.sub(r'^\s*#[^\n]*\n?', '', deliverable.content, count=1)
        return self._convert_markdown(content)

    # -------------------------------------------------------------------------
    # Markdown → ReportLab converter
    # -------------------------------------------------------------------------

    def _convert_markdown(self, markdown_content: str) -> list:
        """Convert a markdown string to a list of ReportLab flowables."""
        flowables: List = []
        lines = markdown_content.split("\n")
        in_code_block = False
        in_yaml = False
        in_table = False
        table_lines: List[str] = []
        code_lines: List[str] = []
        prev_was_bullet = False
        prev_was_numbered = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # YAML front matter
            if i == 0 and stripped == "---":
                in_yaml = True
                i += 1
                continue
            if in_yaml:
                if stripped == "---":
                    in_yaml = False
                i += 1
                continue

            # Horizontal rules — skip
            if re.match(r"^[-*_]{3,}\s*$", stripped):
                i += 1
                continue

            # Code blocks
            if stripped.startswith("```"):
                if in_code_block and code_lines:
                    for cl in code_lines:
                        flowables.append(Paragraph(self._prep(cl[:200]), self.styles["code"]))
                    code_lines = []
                in_code_block = not in_code_block
                i += 1
                continue

            if in_code_block:
                code_lines.append(line[:200])
                i += 1
                continue

            # Tables — flush the accumulated lines when a non-table line is hit
            if stripped.startswith("|") and stripped.endswith("|"):
                if len(stripped) <= 1000:
                    in_table = True
                    table_lines.append(stripped)
                else:
                    if table_lines:
                        self._flush_table(flowables, table_lines)
                        table_lines = []
                    in_table = False
                i += 1
                continue
            elif in_table:
                self._flush_table(flowables, table_lines)
                table_lines = []
                in_table = False
                # fall through to process current line normally

            # Empty line
            if not stripped:
                prev_was_bullet = False
                prev_was_numbered = False
                i += 1
                continue

            # Level-1 headings in deliverable body → render as H2
            h1_match = re.match(r"^#\s+(.+)$", stripped)
            if h1_match:
                text = self._clean_text(h1_match.group(1))
                flowables.append(Paragraph(self._prep(text), self.styles["h2"]))
                flowables.append(Spacer(1, _GAP_AFTER_H2))
                prev_was_bullet = False
                prev_was_numbered = False
                i += 1
                continue

            # Headings level 2–6 — followed by an explicit Spacer
            heading_match = re.match(r"^(#{2,6})\s+(.+)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                text = self._clean_text(heading_match.group(2))
                style_key = {2: "h2", 3: "h3"}.get(level, "h4")
                flowables.append(Paragraph(self._prep(text), self.styles[style_key]))
                flowables.append(Spacer(1, _GAP_AFTER_H3))
                prev_was_bullet = False
                prev_was_numbered = False
                i += 1
                continue

            # Bullet points
            bullet_match = re.match(r"^[-*+]\s+(.+)$", stripped)
            if bullet_match:
                text = self._clean_text(bullet_match.group(1))
                if prev_was_numbered:
                    # Sub-item under numbered list — render as indented bullet
                    flowables.append(
                        Paragraph(f"\u2022  {self._inline_format(text)}", self.styles["sub_bullet"])
                    )
                else:
                    if not prev_was_bullet:
                        flowables.append(Spacer(1, 4))
                    flowables.append(
                        Paragraph(f"\u2022  {self._inline_format(text)}", self.styles["bullet"])
                    )
                    prev_was_bullet = True
                i += 1
                continue

            # Numbered lists
            numbered_match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
            if numbered_match:
                if not prev_was_numbered:
                    flowables.append(Spacer(1, 6))
                num = numbered_match.group(1)
                text = self._clean_text(numbered_match.group(2))
                flowables.append(
                    Paragraph(f"{num}. {self._inline_format(text)}", self.styles["bullet"])
                )
                prev_was_bullet = False
                prev_was_numbered = True
                i += 1
                continue

            # Regular paragraph
            if stripped and len(stripped) <= 2000:
                # Skip dash-heavy lines (stray table separators)
                if stripped.count("-") > 50 and stripped.count("-") / len(stripped) > 0.5:
                    i += 1
                    continue

                if prev_was_numbered or prev_was_bullet:
                    flowables.append(Spacer(1, 6))
                prev_was_bullet = False
                prev_was_numbered = False

                formatted = self._inline_format(self._clean_text(stripped))

                # Pseudo-heading detection: entire line is **bold** with optional trailing colon
                if re.match(r"^\*\*.+\*\*:?\s*$", stripped):
                    flowables.append(Paragraph(formatted, self.styles["body_pseudo_heading"]))
                else:
                    flowables.append(Paragraph(formatted, self.styles["body"]))

            i += 1

        # Flush any remaining table or code block
        if table_lines:
            self._flush_table(flowables, table_lines)
        if code_lines:
            for cl in code_lines:
                flowables.append(Paragraph(self._prep(cl), self.styles["code"]))

        return flowables

    def _flush_table(self, flowables: list, table_lines: List[str]) -> None:
        """Build a table (or action cards) from accumulated lines and append with spacing."""
        raw_headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
        if self._is_action_table(raw_headers):
            card_flowables = self._build_action_cards(table_lines)
            flowables.extend(card_flowables)
            return
        if self._is_roadmap_table(raw_headers):
            card_flowables = self._build_roadmap_cards(table_lines)
            flowables.extend(card_flowables)
            return

        tbl = self._build_table(table_lines)
        if tbl:
            flowables.append(Spacer(1, _GAP_BEFORE_TABLE))
            flowables.append(tbl)
            flowables.append(Spacer(1, _GAP_AFTER_TABLE))

    @staticmethod
    def _is_action_table(raw_headers: List[str]) -> bool:
        """Return True if this is the 7-column action plan table."""
        return len(raw_headers) == 7 and raw_headers[0].strip() == "#"

    @staticmethod
    def _is_roadmap_table(raw_headers: List[str]) -> bool:
        """Return True if this is the 5-column roadmap table."""
        return len(raw_headers) == 5 and raw_headers[0].strip() == "#"

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
                ("LINEBELOW", (0, 0), (0, 0), 0.5, CARD_BORDER),
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
            flowables.append(Spacer(1, _GAP_AFTER_TABLE))

        return flowables

    def _build_roadmap_cards(self, table_lines: List[str]) -> list:
        """Build bordered card flowables from a 5-column roadmap table."""
        rows = []
        for line in table_lines[2:]:
            if re.match(r"^[\|\s:\-]+$", line):
                continue
            if line.count("-") > 100:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) != 5:
                continue
            if any(len(c) > 2000 for c in cells):
                continue
            clean_cells = [self._clean_table_cell(c, 500) for c in cells]
            rows.append(clean_cells)

        if not rows:
            return []

        flowables = []
        card_width = 6.5 * inch

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
            time_est = self._prep(row_data[3])
            what_do = self._prep(row_data[4])

            card_data = [
                [Paragraph(f"{number}. {action}", card_title_style)],
                [Paragraph(f"<b>Tool:</b> {tool}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Time:</b> {time_est}", card_detail_style)],
                [Paragraph(f"<b>What to do:</b> {what_do}", card_detail_style)],
            ]

            card = Table(card_data, colWidths=[card_width])
            card.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.75, CARD_BORDER),
                ("LINEBELOW", (0, 0), (0, 0), 0.5, CARD_BORDER),
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
            flowables.append(Spacer(1, _GAP_AFTER_TABLE))

        return flowables

    # -------------------------------------------------------------------------
    # Table builder
    # -------------------------------------------------------------------------

    def _build_table(self, table_lines: List[str]) -> Optional[Table]:
        """Build a styled ReportLab Table from markdown pipe-table lines."""
        if len(table_lines) < 3:
            return None

        for line in table_lines:
            if len(line) > 1000:
                return None

        raw_headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
        headers = [self._clean_table_cell(h, 100) for h in raw_headers]

        if all(h.startswith("-") or len(h) > 200 for h in raw_headers):
            return None
        if any(len(h) > 500 for h in raw_headers):
            return None

        rows = []
        for line in table_lines[2:]:
            if re.match(r"^[\|\s:\-]+$", line):
                continue
            if line.count("-") > 100:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) != len(headers):
                continue
            if any(len(c) > 2000 for c in cells):
                continue
            clean_cells = [self._clean_table_cell(c, 300) for c in cells]
            if not all(c.startswith("-") for c in cells if c):
                if any(
                    len(c) > 3 and not c.replace("-", "").replace(".", "").strip() == ""
                    for c in clean_cells
                ):
                    rows.append(clean_cells)

        if not headers or not rows:
            return None

        col_width = (6.5 * inch) / len(headers)

        # Use a tighter body style for table cells
        cell_style = ParagraphStyle(
            "PDFTableCell",
            fontName="Helvetica",
            fontSize=10,
            textColor=BODY_GRAY,
            spaceBefore=0,
            spaceAfter=0,
            leading=14,
        )
        header_style = ParagraphStyle(
            "PDFTableHeader",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=DARK_BLUE,
            spaceBefore=0,
            spaceAfter=0,
            leading=14,
        )

        data = [
            [Paragraph(self._prep(h), header_style) for h in headers]
        ] + [
            [Paragraph(self._prep(c), cell_style) for c in row]
            for row in rows
        ]

        tbl = Table(data, colWidths=[col_width] * len(headers))
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), DARK_BLUE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TABLE_ALT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return tbl

    # -------------------------------------------------------------------------
    # Text helpers
    # -------------------------------------------------------------------------

    def _inline_format(self, text: str) -> str:
        """
        Convert markdown inline markers to ReportLab XML markup.

        Sanitizes Unicode, then processes inline formatting in priority order:
        code spans, bold, italic, links. Each segment is XML-escaped individually.
        """
        text = self._sanitize(text)

        result = ""
        i = 0
        while i < len(text):
            ch = text[i]

            # Code span: `...`
            if ch == "`":
                end = text.find("`", i + 1)
                if end != -1:
                    inner = self._esc(text[i + 1 : end])
                    result += f'<font name="Courier" size="10">{inner}</font>'
                    i = end + 1
                    continue

            # Bold: **...**
            if text[i : i + 2] == "**":
                end = text.find("**", i + 2)
                if end != -1:
                    result += f"<b>{self._esc(text[i + 2 : end])}</b>"
                    i = end + 2
                    continue

            # Italic: *...* (single star, not **)
            if ch == "*" and text[i : i + 2] != "**":
                end = text.find("*", i + 1)
                if end != -1 and text[end - 1 : end + 1] != "**":
                    result += f"<i>{self._esc(text[i + 1 : end])}</i>"
                    i = end + 1
                    continue

            # Markdown link: [label](url) → just the label
            if ch == "[":
                link_match = re.match(r"\[([^\]]+)\]\([^)]+\)", text[i:])
                if link_match:
                    result += self._esc(link_match.group(1))
                    i += len(link_match.group(0))
                    continue

            result += self._esc(ch)
            i += 1

        return result

    def _prep(self, text: str) -> str:
        """Sanitize Unicode then XML-escape — safe to use directly in Paragraph markup."""
        return self._esc(self._sanitize(text))

    @staticmethod
    def _sanitize(text: str) -> str:
        """
        Replace Unicode characters that Helvetica (Latin-1) cannot render.

        Applies _UNICODE_MAP first, then replaces any remaining characters
        outside Latin-1 (codepoint > 255) with '?'.
        """
        if not text:
            return ""
        for char, replacement in _UNICODE_MAP.items():
            if char in text:
                text = text.replace(char, replacement)
        return "".join(ch if ord(ch) <= 255 else "?" for ch in text)

    @staticmethod
    def _esc(text: str) -> str:
        """Escape XML special characters for use in ReportLab Paragraph markup."""
        if not text:
            return ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _clean_text(text: str) -> str:
        """Strip markdown link syntax, keeping display text."""
        return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text).strip()

    @staticmethod
    def _clean_table_cell(text: str, max_length: int = 300) -> str:
        """Strip markdown formatting from a table cell and truncate if needed."""
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        if len(text) > max_length:
            text = text[: max_length - 3] + "..."
        return text.strip()

    def _get_output_path(self, company_slug: str, filename: str) -> Path:
        """Return the output path, creating the documents directory if needed."""
        output_dir = self.output_dir / company_slug / "documents"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename
