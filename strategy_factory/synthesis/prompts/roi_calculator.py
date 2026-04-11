"""Prompt for "What It Costs & What You Save" — simple ROI snapshot."""

PROMPT = """
# Task: Generate What It Costs & What You Save

You are an SMB AI strategist writing directly to a business owner.

Based on the action plan and company research provided, show the math on whether AI tools are worth it for this business. Keep it simple — this is a business owner, not a CFO.

## What to produce

### Your Monthly Investment (~100 words)

A table listing the tools recommended in the action plan:

| Tool | Monthly Cost | What It Does |
|------|-------------|--------------|
| [Tool 1] | $X/mo | [One sentence] |
| [Tool 2] | $X/mo | [One sentence] |
| [Tool 3] | $X/mo | [One sentence] |
| **Total new cost** | **$X/mo** | |

Produce this table with at least 3 tool rows plus the total row. Fill every cell.

### What You Get Back (~250 words)

For each major time-saving, show the math:
- Task being automated
- Hours saved per week
- Dollar value at $75-100/hr

Use these SMB AI stats as context — weave them into the narrative where they fit naturally:
- 93% of SMBs using AI for scaling reported revenue growth (41% saw gains over 10%)
- 82% report AI-related cost reductions
- 91% saw year-over-year ROI on AI investments
- Average employee saves 5.6 hours/week with AI
- 2.7x effective FTE capacity gain

Don't list these as bullet points — use them to support your specific calculations for this business.

### When You Break Even (~100 words)

Simple statement with timeframe. "At this rate, the tools pay for themselves in X weeks."

### The Real Calculation (~200 words)

Honest paragraph putting it together with a ratio.

Use this ROI formula: (hours saved/week x $/hr x 52 weeks) - (annual tool cost + setup cost)

Reference this real example to anchor expectations: a property management company invested $81k in AI implementation and saw $215k/yr in impact — that's 166% ROI with a 9-month payback period. Your numbers will be smaller, but the ratio holds.

End with this: "The math works — but only if you actually set things up and use them. Most SMBs buy the tools and never configure them properly. The difference between buying AI tools and getting ROI from them is execution: training, workflow setup, and follow-through. That's where a consultant earns their fee."

## Mandatory rules
- Use round numbers — precision implies false accuracy
- Keep owner's hourly rate at $75-100/hr
- No NPV, no discount rates, no sensitivity analysis, no 3-year TCO
- If uncertain, say "probably" or "depending on your volume"
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Fill every cell in every table. No empty cells.
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
"""
