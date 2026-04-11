"""Prompt for Executive Summary — compelling overview of the full report."""

PROMPT = """
# Task: Generate Executive Summary

Based on the complete AI strategy analysis produced above, create a compelling executive summary that gives the business owner a clear picture of where they stand and what to do next. This is the first section the client will read — it must make them want to keep reading.

## Required Sections

### The Big Picture (~200 words)

A flowing narrative that covers:
- Their single biggest AI opportunity (from the tools audit and pain points)
- Where they're losing the most time/money (from pain points)
- Their readiness level in plain terms (from the readiness assessment)
- What success looks like if they act (from the roadmap and ROI sections)

Write this as connected prose — no bullet points, no headers within this section. Be specific to this business. Use real numbers and tool names from the analysis. This section MUST contain a complete ~200-word narrative. Do NOT output just a heading.

### What To Do This Week (~100 words)

The single most important first action, the tool to use, and how long it takes. One paragraph. Make it feel doable — like something they could start on Monday morning. Name the exact tool and the exact task. This section MUST contain a complete ~100-word paragraph. Do NOT leave it as just a heading.

### The Bottom Line (~100 words)

Two sentences: what it costs per month and what they get back in time and money. Reference the ROI math from the cost section. End with one sentence about why acting now beats waiting — the gap between experimenting with AI and actually capturing value. This section MUST contain a complete ~100-word paragraph. Do NOT leave it as just a heading.

## Output Format
- Write in second person ("you", "your") throughout
- Be specific — name tools, dollar amounts, hours saved
- No jargon, no "digital transformation", no maturity models
- This is the first thing the client reads — make every word count
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Fill every cell in every table. No empty cells.
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
"""
