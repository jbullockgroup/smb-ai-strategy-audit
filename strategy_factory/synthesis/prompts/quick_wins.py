"""Prompt for "What To Do First" — action plan with concrete quick wins."""

PROMPT = """
# Task: Generate What To Do First

You are an SMB AI strategist writing directly to a business owner.

Based on the company research and pain points identified, give this owner 3-5 high-impact actions to take THIS month. Ranked by impact, most valuable first.

## What to produce

### Your Biggest Opportunity Right Now (~100 words)

2-3 sentences identifying the #1 opportunity. Specific to this business. This MUST be a complete paragraph with specific detail. Do not output just a heading.

### Your Top Actions This Month (~400 words)

3-5 actions, each presented as a row in this exact table:

| # | Action | Tool (Price) | Time to Set Up | Weekly Time Saved | What You Get | First Step Today |
|---|--------|-------------|----------------|-------------------|--------------|------------------|
| 1 | [verb-first action] | [Tool $X/mo] | [time] | [X min/day] | [outcome] | [specific thing] |
| 2 | [verb-first action] | [Tool $X/mo] | [time] | [X min/day] | [outcome] | [specific thing] |
| 3 | [verb-first action] | [Tool $X/mo] | [time] | [X min/day] | [outcome] | [specific thing] |
| 4 | [verb-first action] | [Tool $X/mo] | [time] | [X min/day] | [outcome] | [specific thing] |

Produce this table with at least 4 rows. Fill every cell. No empty cells.

If an action would benefit from API integration or automation setup, note it in the First Step column: "Set up [specific thing] — this may require technical assistance."

### Tool Recommendations (~150 words)

Open with BCG's 10-20-70 rule: "70% of AI success comes from people and process, 20% from technology, 10% from algorithms. The tools below are the easy part — training your team and redesigning workflows is where the real ROI lives."

Then recommend:
- **ChatGPT Plus ($20/mo)** — content creation, data analysis, image generation, general tasks
- **Claude Pro ($20/mo)** — long documents, proposals, complex writing, document analysis
- **Claude Max ($100-200/mo)** — for owners who want an AI partner that can handle multi-step work autonomously, analyze files, and manage complex tasks
- **Gemini (free or $20/mo)** — especially for Google Workspace users (Gmail, Docs, Sheets sidebar)
- **Perplexity ($20/mo)** — real-time research, market intelligence, competitive analysis, finding current information
- **n8n** — for automation workflows (self-serve or with setup assistance)
- **Voice AI Agent (Vapi, Retell, or Trillet)** — handles missed calls, books appointments, qualifies leads 24/7. $50-300/mo depending on call volume. Critical for any business that receives phone inquiries.

### Total Monthly Investment (~100 words)

Table:

| Tool | Monthly Cost | What It Does |
|------|-------------|--------------|
| [Tool 1] | $X/mo | [One sentence] |
| [Tool 2] | $X/mo | [One sentence] |
| [Tool 3] | $X/mo | [One sentence] |
| **Total new cost** | **$X/mo** | |

Note that more advanced setups (API integrations, custom workflows, employee training) are one-time investments, not monthly costs.


## Mandatory rules
- Every action must have a specific tool name and price
- Tables must be complete — no empty cells
- If an action requires technical help, say so clearly
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Fill every cell in every table. No empty cells.
- **Use these tools:** ChatGPT Plus ($20/mo), Claude Pro ($20/mo), Claude Max ($100-200/mo), Gemini ($0-20/mo), Perplexity ($20/mo), n8n for automation, native integrations first
- **Never recommend:** Make.com or Zapier, enterprise platforms or complex SaaS without specific names, "AI platforms" without a specific product name. API integrations, n8n workflows, and custom automation are fair game.
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
"""
