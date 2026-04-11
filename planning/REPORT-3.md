# REPORT-3: DocX, PDF & UI Fix List

## PDF Fixes
1. **TOC missing closing section** — "Putting It All Together" appears in DocX TOC and UI but not in PDF Table of Contents. The section content renders fine; just needs a TOC entry.
2. **Line breaks around tables and cards** — Add line break before AND after tables and cards in the PDF.
3. **Missing headings** — Some markdown headings that appear in DocX are not rendering in the PDF.

## DocX Fixes
4. **Tighten blank gaps** — In "Where You Stand Today," there are large blank gaps before "Your Current Tool Stack" heading and before the tools table. Remove excess whitespace.
5. **Markdown leaking through** — H1 (`#`) heading markers appearing as literal text. Fix markdown-to-DocX conversion so heading syntax is stripped/rendered properly.
6. **Table header styling** — Add background color to table header rows to match the PDF appearance.
7. **Line breaks around bullet points** — Add line break before and after each bullet point in DocX.
8. **Line breaks around tables** — Add line break before tables (after already exists).

## Both DocX & PDF
9. **Numbered list formatting** — Add line breaks before and after each numbered item.
10. **No nested bullets rule** — No bulleted lists inside numbered lists, no bulleted lists inside other bulleted lists. Flatten any nesting.
11. **Line breaks around cards** — Add line break before and after "card" elements in both formats.

## UI Fixes
12. **Total cost rounding** — Round to nearest cent (e.g., $0.09 not $0.0859).
13. **Total cost accuracy** — Formula is significantly off (showed ~$0.09 when actual was $0.13). Review token counts/exchange and adjust the cost formula accordingly.
