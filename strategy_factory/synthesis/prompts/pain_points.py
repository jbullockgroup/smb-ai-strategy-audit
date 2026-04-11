"""Prompt for "Where You're Losing Money" — daily pain points and time wasters."""

PROMPT = """
# Task: Generate Where You're Losing Money

You are an SMB AI strategist writing directly to a business owner.

Based on the company research provided, write a plain-English breakdown of where this business is wasting time and money.

## What to produce

### The 500 Customer Test (~150 words)

Open with this thought experiment: "Imagine you woke up tomorrow with 500 new customers. What breaks first?"

Then answer it specifically for this business in 2-3 sentences naming the specific bottleneck. Write the full answer — do not leave this section as just a heading or the question alone.

### Your Time-Wasters Ranked (~200 words)

Top 5 list with hours/week and dollar value at $75-100/hr. Format as this exact table:

| Rank | Task | Hours/Week Lost | Dollar Value/Week |
|------|------|----------------|-------------------|
| 1 | [specific task] | [X hrs] | $[Y] |
| 2 | [specific task] | [X hrs] | $[Y] |
| 3 | [specific task] | [X hrs] | $[Y] |
| 4 | [specific task] | [X hrs] | $[Y] |
| 5 | [specific task] | [X hrs] | $[Y] |

Produce this exact table with 5 rows. Fill every cell. No empty cells. Highest impact first.

### Your Highest-Impact Workflows (~400 words)

Open with the workflow redesign principle: "If you were building this process from scratch today with AI available, what would it look like? That's the right mindset — don't bolt AI onto old processes, redesign them."

Use these 7 diagnostic questions INTERNALLY to determine which workflows apply to this business. Do NOT output these questions — they are your reasoning framework, not your output:
1. Where's the bottleneck?
2. What breaks first under pressure?
3. What mistakes happen daily?
4. Where does time go?
5. Where's the profit opportunity?
6. Where is expertise being misused?
7. What's repeated every day?

For each of these 6 that applies to this business, write a mini-analysis:

1. **Speed to Lead** — Are inquiries going unanswered for hours? What's the cost?
2. **Follow-Up Sequences** — Are leads falling through the cracks after first contact?
3. **Database Reactivation** — Is there a customer list that hasn't been contacted in 90+ days?
4. **Internal Reporting** — Who's spending time pulling numbers together that could be automated?
5. **Document Processing** — Proposals, contracts, estimates — how much manual work goes into each one?
6. **Phone & Call Management** — Are incoming calls going to voicemail? Are after-hours inquiries being lost? How much revenue walks out the door with every missed call?

ROI example: 62% of calls to small businesses go unanswered. A voice AI agent can handle after-hours inquiries, book appointments, and qualify leads 24/7 — one dental practice recovered $47k/year in missed-call revenue.

For each, provide:
- What's happening now (specific to this business)
- What AI could do
- A real example with a number
- Whether this is something the owner can set up themselves or would benefit from expert setup

Embed this principle: "Audit why before what." Example: one e-commerce company thought they needed an AI content writer — they actually needed their product feed integrated with their email platform. Result: 8 hours/week saved at zero new tool cost. Diagnosis matters more than tool selection.

Use these real ROI numbers as examples — adapt them to this business, don't copy them verbatim:
- Dental speed-to-lead: 12% to 25% conversion, same ad spend, +13 patients/mo
- Document processing: saves 13min/doc, which adds up to $70k+/yr
- Follow-up sequences: webinar conversion 4% to 12%
- Database reactivation: 2-3% of dormant contacts = $32-48k recovered
- Reporting automation: $12k/mo in error reduction

### The Content Creation Gap (~200 words)

Where they're falling short (social, email, blog, reviews), opportunity cost, and why this is an easy win with AI.

If digital presence or online activity data appears in the research context above, reference specific facts: posting frequency, platform activity, or content gaps found during research.

If customer review data appears in the research (from the social_reviews query), reference it directly: mention specific complaint themes, praise themes, review volume, or ratings. Frame complaints as pain points that AI can address and praise as strengths to protect.

If the research context includes a "Blog & Content" section that says "No significant blog or content marketing presence found", flag this explicitly as a gap that AI content tools can fill quickly — blog posts, email newsletters, and social content can be bootstrapped with AI in hours, not weeks.

Note that content workflows can be set up quickly with the right prompting strategy — this is a good candidate for a training session.

### What Your Competitors Are Up To (~100-150 words)

If the research context above mentions specific competitors or alternative businesses, write a brief competitive pressure section. For each named competitor (up to 3), mention:
- Their name and what they do
- Any AI or automation they appear to be using
- What this means for the reader (one sentence about the competitive gap)

If no specific competitors were found in research, write one paragraph about the general competitive pressure in this industry: "Your competitors are already adopting AI tools — [industry] businesses using AI report [specific benefit from research]. The gap between early adopters and wait-and-see businesses grows every quarter."

### Your Industry's AI Moment (~150-200 words)

Write 2-3 paragraphs about the current AI momentum in this industry. Use the research data about industry AI adoption rates, recent AI tool launches for this sector, and competitive shifts. Cover:
- What percentage of similar businesses are now using AI (cite from research if available)
- What's changed in the last 6-12 months (new tools, platform updates, customer expectations)
- Why waiting is now the riskier choice than experimenting

End with: "The businesses that figure this out in the next 90 days will have a 12-18 month head start on the ones still 'watching and waiting.'"

This section must be grounded in the research provided above. If specific adoption rates are available, use them. If not, reference the general trend that AI adoption among SMBs has doubled in the past year and that late adopters are falling behind.

## Mandatory rules
- Every section must end with a complete sentence.
- Never truncate mid-table or mid-section.
- Use the embedded ROI numbers as examples — adapt them to this business, don't copy them verbatim.
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Fill every cell in every table. No empty cells.
- Write directly to the owner
- No jargon: no "department matrices", "ADKAR", "cross-functional analysis"
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
"""
