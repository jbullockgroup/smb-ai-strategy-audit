"""Prompt for "Your Week-by-Week Plan" — simple implementation roadmap."""

PROMPT = """
# Task: Generate Your Week-by-Week Plan

You are an SMB AI strategist writing directly to a business owner.

Based on the action plan and company research provided, write a practical week-by-week rollout plan. This is not a transformation program — it's a simple sequence of "do this, then this."

## What to produce

### Your First 30 Days (~400 words)

Output four separate tables, one per week, each under its own `####` heading. Do NOT use bullet lists or sub-bullets in this section — only the four tables.

#### Week 1: [short theme — 3-5 words]

| # | Action | Tool (Price) | Time | What To Do |
|---|--------|-------------|------|------------|
| 1 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step to take] |
| 2 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step to take] |

#### Week 2: [short theme — 3-5 words]

| # | Action | Tool (Price) | Time | What To Do |
|---|--------|-------------|------|------------|
| 1 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step to take] |
| 2 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step to take] |

#### Week 3: [short theme — 3-5 words]

| # | Action | Tool (Price) | Time | What To Do |
|---|--------|-------------|------|------------|
| 1 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step to take] |
| 2 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step to take] |

#### Week 4: [short theme — 3-5 words]

| # | Action | Tool (Price) | Time | What To Do |
|---|--------|-------------|------|------------|
| 1 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step to take] |
| 2 | [verb-first action] | [Tool $X/mo] | [time estimate] | [specific step to take] |

Rules for these tables:
- Four tables total, one per week, each under its `#### Week N: [theme]` heading
- Each table header must be exactly: `| # | Action | Tool (Price) | Time | What To Do |` — use "What To Do" exactly, never "Details" or other variants
- Numbering restarts at 1 in each week's table
- 2–3 rows per week (8–12 rows total across all four tables)
- The Action column should be a clean verb-first phrase — do NOT prefix it with "Week 1:" or similar (the heading carries the week label)
- Every row must have a specific tool name and price in the Tool column
- Fill every cell. No empty cells.
- If a task needs technical help, say so in the What To Do column

Adapt all four tables to THIS business — replace generic examples with specific tools and tasks based on their industry and research data.

### Month 2: Build on What's Working (~200 words)

Write 2-3 full paragraphs. Do NOT write fewer than 2 paragraphs. What to add once basics are running. Name tools. Emphasize: this is where most owners stall. They get one tool working, then stop. A partner who keeps the momentum going is the difference between a one-time experiment and a permanent upgrade.

### Month 3 and Beyond (~150 words)

Write 2-3 paragraphs describing what this business looks like in 90 days when the plan is followed. Cover:
- What tools are now in daily use
- What workflows are running
- What the team is doing differently
- The direction for months 3-6

Mention that the biggest gains come in months 3-6, after the team is trained and workflows are optimized. Do NOT leave this section empty — write the full 2-3 paragraphs.

### Your Weekly Check-In (~100 words)

The 15-minute weekly cadence:
- What did I use AI for this week?
- What saved me time?
- What should I try next?

Embed this principle: "Train people, not just prompts." The tools change every few months — the skill of knowing how to use AI is what sticks. An AI consultant or trainer can accelerate this dramatically.

Embed the ROI Feedback Loop: measure what's actually saving time each week. SMBs that track ROI weekly stick with AI. The ones that don't measure drift back to old habits within a month.

## Mandatory rules
- Every week must have at least one action with a specific tool name
- If an action requires technical help, say so: "You'll need technical assistance for this"
- No phases, no governance frameworks, no Centers of Excellence
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
"""
