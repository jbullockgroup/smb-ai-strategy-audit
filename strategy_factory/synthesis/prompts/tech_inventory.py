"""Prompt for "Where You Stand Today" — tools audit and AI opportunity map."""

PROMPT = """
# Task: Generate Where You Stand Today

You are an SMB AI strategist writing directly to a business owner.

Based on the company research provided, write a practical assessment of this business's current tools and hidden AI opportunities.

## What to produce

### Your Current Tool Stack (~350 words)

Open with this: "Many small businesses already have shadow AI — tools employees are using without anyone formally approving them. You probably do too."

Then follow with this principle: "Before buying anything new, activate what you already own."

Create this exact table:

| Tool | What You Use It For | AI Feature Already Built In | What It Could Do For You |
|------|--------------------|-----------------------------|--------------------------|
| [Google Workspace or Microsoft 365] | [what this business uses it for] | [specific feature: Help me write, Gemini sidebar, Smart Compose, Copilot] | [one concrete capability] |
| [Accounting software] | [usage] | [specific AI feature] | [concrete capability] |
| [Website platform] | [usage] | [specific AI feature] | [concrete capability] |
| [Scheduling/booking tool] | [usage] | [specific AI feature] | [concrete capability] |
| [CRM or customer list] | [usage] | [specific AI feature] | [concrete capability] |
| [Industry-specific software] | [usage] | [specific AI feature] | [concrete capability] |
| [Social media / scheduling tool] | [usage] | [specific AI feature] | [concrete capability] |
| Phone system (landline, VoIP, Google Voice, RingCentral) | [usage] | [specific AI feature] | [concrete capability] |
| Voice AI / answering service | [usage] | [specific AI feature] | [concrete capability] |

Produce this exact table with 9 rows. Fill every cell. If research returns nothing about a specific tool, infer based on industry and company size. Say "based on typical [industry] businesses your size, you're likely using..." rather than skipping it.

For each tool, name the actual AI feature built into it. Be specific — "Help me write in Gmail" not "AI writing features."

### What to Automate (~250 words)

List 6-8 tasks this business is almost certainly doing by hand. Format each as:
- **[Task]** — [Time it takes] — [What AI does instead]

Be specific to their industry. Include this example if relevant:
- **Answering calls and booking appointments** — [X hours/week] — Voice AI agent handles scheduling, after-hours, and overflow

For items that would require setup help, add: "(requires configuration)" or "(can be automated with the right setup)."

Use the AI Suitability Filter as your screening principle: a task is worth automating if it has structured input, predictable output, rule-based decisions, and happens repeatedly. Use this to explain why certain manual tasks are prime AI candidates — if a task meets 3 or more of these criteria, call it out.

### Your #1 AI Opportunity (~150 words)

This section MUST contain a complete 3-5 sentence paragraph. DO NOT output just a heading.

3-5 sentence paragraph identifying the single biggest opportunity for THIS business. End with one declarative sentence. Hint at the gap between seeing the opportunity and capturing it — most owners know where AI could help but struggle to implement it properly.

## Mandatory rules
- Every section must end with a complete sentence.
- Never truncate mid-table or mid-section.
- If you run out of research data for a specific item, say so plainly rather than skipping it.
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Fill every cell in every table. No empty cells.
- Write directly to the owner: "You're probably using..." not "The company uses..."
- No jargon: no "digital transformation", "AI maturity", "tech stack assessment"
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
"""
