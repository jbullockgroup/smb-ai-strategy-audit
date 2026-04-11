"""Prompt for "Your AI Readiness" — simple readiness scorecard."""

PROMPT = """
# Task: Generate Your AI Readiness

You are an SMB AI strategist writing directly to a business owner.

Based on the research and tools audit provided, assess where this business stands and give them a simple readiness score.

## What to produce

### Where You Stand (~100 words)

3-4 sentence narrative placing the business in context. Do NOT start with "You're in a common spot." Instead, lead with the specific reality: what's working in their favor and what's holding them back. Be direct. Name what they have going for them and what's costing them.

Embed the AI Value Gap: "88% of organizations use AI in some form, but only 5-8% are capturing significant business value from it." Use this to frame why readiness matters — it's not about adoption, it's about execution.

### Your Readiness Scorecard (~350 words)

Score the business on 5 dimensions, each 1-5 (total /25):

**1. Current AI Adoption (1-5)**
- 1: Not using any AI tools yet
- 2: Using free AI tools occasionally
- 3: Paying for at least one AI tool and using it regularly
- 4: Using AI tools daily across multiple tasks
- 5: AI integrated into daily operations across multiple team members

**2. Pain Awareness (1-5)**
- 1: Not sure where time is being wasted
- 2: Know the general areas but haven't measured
- 3: Can name specific tasks that eat hours each week
- 4: Have a clear picture of time costs and what to fix
- 5: Have quantified the dollar cost of manual work and prioritized fixes

**3. Digital Foundation (1-5)**
- 1: Still using paper or spreadsheets for most things
- 2: Have basic digital tools (email, maybe a website)
- 3: Using cloud-based software for key operations
- 4: Systems are connected and data is accessible
- 5: Connected systems with clean data, ready for automation

**4. Owner Openness (1-5)**
- 1: Skeptical or resistant to new tools
- 2: Curious but haven't tried much
- 3: Have tried a few things, open to more
- 4: Actively looking for tools that save time
- 5: Actively investing time and money in AI adoption

**5. Budget Alignment (1-5)**
- 1: Can't allocate anything for new tools right now
- 2: Could do $20-50/month if it clearly paid off
- 3: Comfortable with $50-150/month for the right tools
- 4: Ready to invest $150+/month to solve real problems
- 5: Budget allocated and ready to invest in tools, training, and implementation

Present the scores as this exact table:

| Dimension | Score (1-5) | Explanation |
|-----------|:-----------:|-------------|
| 1. Current AI Adoption | [1-5] | [One sentence based on research] |
| 2. Pain Awareness | [1-5] | [One sentence based on research] |
| 3. Digital Foundation | [1-5] | [One sentence based on research] |
| 4. Owner Openness | [1-5] | [One sentence based on research] |
| 5. Budget Alignment | [1-5] | [One sentence based on research] |
| **Total** | **[sum]/25** | |

You MUST produce all 5 dimensions. Do not skip any dimension. Fill every cell.
Verify that your total equals the sum of the 5 individual scores.

### What Your Score Means (~150 words)

Three tiers:

**5-10: Not Ready Yet**
"The good news is you haven't wasted money on the wrong tools yet. The right move is to get a clear picture of where AI fits your specific business before buying anything."

**11-17: Ready to Start**
"You've got the foundation. The gap between where you are and where you could be is mostly about execution — setting up the right workflows and training your team to use them daily."

**18-25: Ready to Scale**
"You're ahead of most SMBs. The next step is optimizing what's working and building more sophisticated automations."

Embed this stat: "Organizations scoring above 70% readiness are 3x more likely to see meaningful ROI within 12 months."

Reference the AI Maturity Curve: Hype -> Pilot -> Habit -> Scale. Place this business on it and explain what it means for their next steps.

### Bottom Line (~50 words)

One sentence: "Based on what I know about [company], you're scoring approximately X/25, which means..."

## Mandatory rules
- Infer scores from the research — don't ask for answers
- Be direct about the score, not wishy-washy
- No radar charts, no peer comparison tables
- Use plain text arrows (->) not Unicode arrows
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Fill every cell in every table. No empty cells.
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
"""
