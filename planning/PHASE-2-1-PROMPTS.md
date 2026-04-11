# Plan: Rewrite All 6 Synthesis Prompts

## Context

The current prompts produce generic output because they give Gemini a *topic* but no *point of view*. The consulting guides contain real ROI numbers, proven frameworks, named workflows, and specific stats — but none of that material is embedded in the prompts. PHASE-2.md identified this and designed a fix (per-section word budgets, embedded stats, explicit table schemas). This plan implements that rewrite for all 6 existing prompt files.

The original enterprise prompts were 2,400–7,700 words of corporate bloat. The current prompts are 300–600 words of generic instructions. The target is the middle ground: **enterprise-grade evidence, SMB-grade delivery**.

## User Directives

1. **Quick wins must use tables** — like the original enterprise prompts (structured rows, not bullet lists)
2. **Remove "no API required" criterion** — things requiring API/developer help are fair game
3. **Remove "you're in a common spot" framing** in maturity assessment — replace with something stronger
4. **Update tool recommendations** — add Perplexity ($20/mo), add Claude Max ($100-200/mo) alongside Claude Pro ($20/mo)
5. **Reframe from "do it yourself" to "here's what a consultant helps you do"** — the audit is a sales tool. The output should leave the owner understanding the value of expert guidance, not just holding a to-do list. This means: emphasizing training, surfacing where implementation is not DIY, and positioning AI consulting as an ongoing partnership rather than a one-time assessment.

---

## Files to Modify

All files are in `strategy_factory/synthesis/prompts/`:

1. `tech_inventory.py`
2. `pain_points.py`
3. `quick_wins.py`
4. `roadmap.py`
5. `maturity_assessment.py`
6. `roi_calculator.py`

No config changes, no new files, no orchestrator changes. Just the 6 prompt rewrites.

---

## Prompt 1: `tech_inventory.py` — "Where You Stand Today"

**Target: 800–1,000 words**

### Structure

```
## Role
One line: SMB AI strategist writing directly to the business owner.

## What to produce

### Your Current Tool Stack (~350 words)
Table with 4 columns: Tool | What You Use It For | AI Feature Already Built In | What It Could Do For You

Required rows (infer based on industry if research is thin):
- Google Workspace or Microsoft 365 → name Help me write, Gemini sidebar, Smart Compose, Copilot
- Accounting software → QuickBooks, FreshBooks, etc.
- Website platform → Shopify, WordPress, Squarespace, Wix
- Scheduling/booking tool → Calendly, Acuity
- CRM or customer list → even if just a spreadsheet
- Industry-specific software
- Social media accounts

Embed this stat in the section intro: "67% of SMBs have shadow AI — tools employees use without approval. You probably do too."

Embed this principle: "Activate what you already own before buying new tools."

Fallback instruction: "If research returns nothing about a specific tool, infer based on industry and company size."

### What's Still Manual (~250 words)
6-8 bullet items. Format: Task — Time it takes — What AI does instead
Specific to their industry. For items that would require setup help, add a note: "requires configuration" or "can be automated with the right setup."

Embed the AI Suitability Filter as a screening principle: a task is worth automating if it has structured input, predictable output, rule-based decisions, and happens repeatedly. Use this to explain why certain manual tasks are prime AI candidates.

### Your #1 AI Opportunity (~150 words)
3-5 sentence paragraph identifying the single biggest opportunity for THIS business.
Ends with one declarative sentence. Hint at the gap between knowing the opportunity and capturing it — most owners see the opportunity but struggle to implement.

## Mandatory rules
- Every section must end with a complete sentence.
- Never truncate mid-table or mid-section.
- If you run out of research data for a specific item, say so plainly rather than skipping it.
- Total length: 800-1,000 words
- Write directly to the owner: "You're probably using..." not "The company uses..."
- No jargon: no "digital transformation", "AI maturity", "tech stack assessment"
```

### Embedded consulting guide material
- Shadow AI stat (67%) — from smb-ai-playbook
- "Activate what you already own" principle — from built-500-ai-workflows
- Specific Google Workspace AI features — from ai-smb-gws
- AI Suitability Filter (structured input, predictable output, rule-based decisions, repeated often) — embedded in "What's Still Manual" section — from how-to-perform-ai-audits

---

## Prompt 2: `pain_points.py` — "Where You're Losing Money"

**Target: 900–1,200 words**

### Structure

```
## Role
One line: SMB AI strategist writing directly to the business owner.

## What to produce

### The 500 Customer Test (~150 words)
Same framing as current prompt. Answer specifically for this business.

### Your Time-Wasters Ranked (~200 words)
Top 5 list with hours/week and dollar value at $75-100/hr.
Format as a table: Task | Hours/Week Lost | Dollar Value/Week

### Your Highest-Impact Workflows (~400 words)
Renamed from "The 5 Boring Workflows." Open with the workflow redesign principle: "If you were building this process from scratch with AI available, what would it look like?" This is the right mindset — don't bolt AI onto old processes, redesign them.

Use these 7 diagnostic questions to determine which workflows apply and why:
1. Where's the bottleneck?
2. What breaks first under pressure?
3. What mistakes happen daily?
4. Where does time go?
5. Where's the profit opportunity?
6. Where is expertise being misused?
7. What's repeated every day?

For each of these 5 that applies to this business:

1. Speed to Lead
2. Follow-Up Sequences
3. Database Reactivation
4. Internal Reporting
5. Document Processing

Each gets a mini-structure:
- What's happening now (specific to this business)
- What AI could do
- Real example with a number
- Whether this is something the owner can set up themselves or would benefit from expert setup

Embed this principle: "Audit why before what." Example: one e-commerce company thought they needed an AI content writer — they actually needed their product feed integrated with their email platform. Result: 8 hours/week saved at zero new tool cost. Diagnosis matters more than tool selection.

Embed these real ROI numbers as examples for Gemini to adapt:
- Dental speed-to-lead: 12%→25% conversion, same ad spend, +13 patients/mo
- Document processing: saves 13min/doc → $70k+/yr
- Follow-up: webinar conversion 4%→12%
- Database reactivation: 2-3% of dormant contacts = $32-48k recovered
- Reporting: $12k/mo error reduction

### The Content Creation Gap (~200 words)
Where they're falling short (social, email, blog, reviews), opportunity cost, why this is an easy win with AI. Note that content workflows can be set up quickly with the right prompting strategy — this is a good candidate for a training session.

## Mandatory rules
- Every section must end with a complete sentence.
- Never truncate mid-table or mid-section.
- Use the embedded ROI numbers as examples — adapt them to this business, don't copy them verbatim.
- Total length: 900-1,200 words
- Write directly to the owner
- No jargon: no "department matrices", "ADKAR", "cross-functional analysis"
```

### Embedded consulting guide material
- Real ROI numbers — from built-500-ai-workflows
- ROI formula: `(time waste × people × days × loaded $/hr) + lost revenue` — from how-to-perform-ai-audits
- "Audit why before what" principle + e-commerce example (8hrs/wk saved at $0 cost) — embedded in workflows section — from what-an-ai-audit-really-is
- 7 diagnostic questions (bottleneck, breaks, mistakes, time waste, profit, expertise misuse, repetition) — embedded in workflows section — from 7-workflow-questions
- Workflow redesign principle ("from scratch with AI") — embedded in workflows section — from smb-ai-value-playbook / McKinsey finding

---

## Prompt 3: `quick_wins.py` — "What To Do First"

**Target: 700–900 words**

### Key changes from current
1. **Actions in tables** — each action gets a structured table row, not bullet list
2. **Remove "anything requiring API knowledge or developer help" from never-recommend list**
3. **Updated tool list** — add Perplexity, add Claude Max tier
4. **Consultant framing** — actions should distinguish between "do it yourself" and "get help setting this up"

### Structure

```
## Role
One line: SMB AI strategist writing directly to the business owner.

## What to produce

### Your Biggest Opportunity Right Now (~100 words)
2-3 sentences identifying the #1 opportunity. Specific to this business.

### Your Top Actions This Month (~400 words)
3-5 actions, each presented as a table row:

| # | Action | Tool (Price) | Time to Set Up | Weekly Time | What You Get | First Step Today |
|---|--------|-------------|----------------|-------------|--------------|------------------|
| 1 | [verb-first name] | [Tool $X/mo] | [30 min / 2 hrs / etc.] | [X min/day] | [concrete outcome] | [one specific thing] |
| 2 | ... | ... | ... | ... | ... | ... |

If an action would benefit from API integration or automation setup, note it in the First Step column: "Set up [specific thing] — this may require technical assistance"

### Tool Recommendations (~150 words)
Short section naming the recommended tools and why. Open with BCG's 10-20-70 rule: 70% of AI success comes from people and process, 20% from technology, 10% from algorithms. The tools below are the easy part — training your team and redesigning workflows is where the real ROI lives.
- ChatGPT Plus ($20/mo) — content creation, data analysis, image generation, general tasks
- Claude Pro ($20/mo) — long documents, proposals, complex writing, document analysis
- Claude Max ($100-200/mo) — for owners who want an AI partner that can handle multi-step work autonomously, analyze files, and manage complex tasks
- Gemini (free or $20/mo) — especially for Google Workspace users (Gmail, Docs, Sheets sidebar)
- Perplexity ($20/mo) — real-time research, market intelligence, competitive analysis, finding current information
- n8n — for automation workflows (self-serve or with setup assistance)

### Total Monthly Investment (~100 words)
Table: Tool | Monthly Cost | What It Does
Note that more advanced setups (API integrations, custom workflows, employee training) are one-time investments, not monthly costs.

## Tool preferences
**Use these tools:**
- ChatGPT Plus ($20/mo), Claude Pro ($20/mo), Claude Max ($100-200/mo), Gemini ($0-20/mo), Perplexity ($20/mo)
- n8n for automation
- Native integrations first

**Never recommend:**
- Make.com or Zapier
- Enterprise platforms or complex SaaS without specific names
- "AI platforms" without a specific product name
- Note: API integrations, n8n workflows, and custom automation are all fair game

## Mandatory rules
- Every action must have a specific tool name and price
- Tables must be complete — no empty cells
- If an action requires technical help, say so clearly
- Total length: 700-900 words
```

### Embedded consulting guide material
- "Activate existing tools first" principle — from 90-day-ai-playbook
- Budget tiers: Starter ($200-500), Standard ($500-1k) — from 30-day-ai-pilot
- BCG 10-20-70 rule (70% people/process, 20% tech, 10% algorithms) — embedded in Tool Recommendations — from smb-ai-value-playbook

---

## Prompt 4: `roadmap.py` — "Your Week-by-Week Plan"

**Target: 800–1,100 words**

### Key changes from current
1. **Add weekly check-in section** — the 15-minute cadence from consulting guides
2. **Consultant touchpoints** — weave in moments where outside help accelerates progress
3. **Employee training emphasis** — "train people not just prompts"

### Structure

```
## Role
One line: SMB AI strategist writing directly to the business owner.

## What to produce

### Your First 30 Days (~400 words)
4 weeks, 2-3 tasks per week. Each task has: action, specific tool, time estimate.

Week 1: Activate existing tools + audit shadow AI
  - "Open your Google Workspace / Microsoft 365 admin panel and turn on [specific AI feature]"
  - "Ask your team: which of you are already using ChatGPT or similar? Make a list."
  - Note: This is a good time to bring in someone who knows the tool landscape to make sure you're not missing anything.

Week 2: Set up first AI tool
  - Name the specific tool and what to do with it
  - "Spend 30 minutes learning the basics. If you want a jumpstart, a one-hour training session can save you weeks of trial and error."

Week 3: Build first workflow
  - If the workflow involves automation or API connections: "This is where setup assistance pays for itself — connecting tools properly the first time avoids rework."
  - If it's a prompting/content workflow: "Get the team involved — the real ROI comes when your employees use AI daily, not just you."

Week 4: Measure and adjust
  - "Spend 15 minutes on this check-in: What did I use AI for? What saved time? What should I try next?"

### Month 2: Build on What's Working (~200 words)
2-3 paragraphs. What to add once basics are running. Name tools.
Emphasize: this is where most owners stall. They get one tool working, then stop. A partner who keeps the momentum going is the difference between a one-time experiment and a permanent upgrade.

### Month 3 and Beyond (~150 words)
What the business looks like in 90 days. Direction, not predictions. Mention that the biggest gains come in months 3-6, after the team is trained and workflows are optimized.

### Your Weekly Check-In (~100 words)
NEW section. The 15-minute weekly cadence:
- What did I use AI for this week?
- What saved me time?
- What should I try next?

Embed the principle: "Train people, not just prompts." The tools change — the skill of knowing how to use AI is what sticks. An AI consultant or trainer can accelerate this.

Embed the ROI Feedback Loop: measure what's actually saving time each week. SMBs that track ROI weekly stick with AI. The ones that don't measure drift back to old habits within a month.

## Mandatory rules
- Every week must have at least one action with a specific tool name
- If an action requires technical help, say so: "You'll need technical assistance for this"
- No phases, no governance frameworks, no Centers of Excellence
- Total length: 800-1,100 words
```

### Embedded consulting guide material
- 30-day pilot structure — from 30-day-ai-pilot
- 90-day framework — from 90-day-ai-playbook
- "Train people not just prompts" weekly check-in — from 90-day-ai-playbook
- 80/15/5 resource allocation rule — from smb-ai-playbook
- ROI Feedback Loop (weekly measurement prevents drift) — embedded in Weekly Check-In — from smb-ai-playbook

---

## Prompt 5: `maturity_assessment.py` — "Your AI Readiness"

**Target: 600–800 words**

### Key changes from current
1. **Remove "You're in a common spot..." opening** — replace with a direct assessment
2. **Change scoring from 0-3 to 1-5** (total /25 instead of /15)
3. **Add maturity curve framing and embedded stat**
4. **Consultant framing** — the "what your score means" section should naturally lead to "here's the kind of help that moves the needle"

### Structure

```
## Role
One line: SMB AI strategist writing directly to the business owner.

## What to produce

### Where You Stand (~100 words)
3-4 sentence narrative placing the business in context. Do NOT start with "You're in a common spot." Instead, lead with the specific reality: what's working in their favor and what's holding them back. Be direct. Name what they have going for them and what's costing them.

Embed the AI Value Gap: "88% of organizations use AI in some form, but only 5-8% are capturing significant business value from it." Use this to frame why readiness matters — it's not about adoption, it's about execution.

### Your Readiness Scorecard (~350 words)
Score the business on 5 dimensions, each 1-5 (total /25):

1. Current AI Adoption (1-5)
   Rubric with 5 levels from "no AI tools" to "daily use across multiple tasks"

2. Pain Awareness (1-5)
   Rubric from "not sure where time is wasted" to "clear picture of costs and fixes"

3. Digital Foundation (1-5)
   Rubric from "paper/spreadsheets" to "connected systems, accessible data"

4. Owner Openness (1-5)
   Rubric from "resistant" to "actively seeking tools"

5. Budget Alignment (1-5)
   Rubric from "no budget" to "ready to invest $150+/mo"

For each: explain the score in one sentence based on research data. Make your best inference.

### What Your Score Means (~150 words)
Three tiers recalibrated for /25:
- 5-10: Not Ready Yet — "The good news is you haven't wasted money on the wrong tools yet. The right move is to get a clear picture of where AI fits your specific business before buying anything."
- 11-17: Ready to Start — "You've got the foundation. The gap between where you are and where you could be is mostly about execution — setting up the right workflows and training your team to use them daily."
- 18-25: Ready to Scale — "You're ahead of most SMBs. The next step is optimizing what's working and building more sophisticated automations."

Embed this stat: "Organizations scoring above 70% readiness are 3x more likely to see meaningful ROI within 12 months."

Reference the AI Maturity Curve: Hype → Pilot → Habit → Scale. Place this business on it.

In each tier, subtly suggest that outside guidance accelerates the journey — "the gap is mostly about execution," "optimizing what's working," etc.

### Bottom Line (~50 words)
One sentence: "Based on what I know about [company], you're scoring approximately X/25, which means..."

## Mandatory rules
- Infer scores from research — don't ask for answers
- Be direct about the score, not wishy-washy
- No radar charts, no peer comparison tables
- Total length: 600-800 words
```

### Embedded consulting guide material
- 5-dimension readiness framework — from ai-readiness-score
- "3x success rate for >70% scores" stat — from ai-readiness-score
- AI Maturity Curve (Hype → Pilot → Habit → Scale) — from smb-ai-playbook
- AI Value Gap stat (88% use AI, only 5-8% capture value) — embedded in "Where You Stand" — from smb-ai-value-playbook

---

## Prompt 6: `roi_calculator.py` — "What It Costs & What You Save"

**Target: 500–700 words**

### Key change from current
**Add a "Getting Help" line item** — frame consulting/training as an investment with its own ROI, not a hidden cost. This is where the business case for the consultant lives.

### Structure

```
## Role
One line: SMB AI strategist writing directly to the business owner.

## What to produce

### Your Monthly Investment (~100 words)
Table: Tool | Monthly Cost | What It Does | Already Paying?

Note which tools they may already be paying for that have AI features included (no new cost).

### What You Get Back (~250 words)
For each time-saving: task, hours saved/week, dollar value at $75-100/hr.

Embed these SMB AI stats as context for Gemini:
- 93% of SMBs using AI for scaling reported revenue growth (41% saw gains >10%)
- 82% report AI-related cost reductions
- 91% saw year-over-year ROI on AI investments
- Average employee saves 5.6 hours/week with AI
- 2.7x effective FTE capacity gain

### When You Break Even (~100 words)
Simple statement with timeframe. "At this rate, the tools pay for themselves in X weeks."

### The Real Calculation (~200 words)
Honest paragraph putting it together with a ratio.
Embed ROI formula: `(hrs saved/wk × $/hr × 52 weeks) - (annual tool cost + setup)`

Reference real example: property management company — $215k/yr impact, $81k investment, 166% ROI, 9-month payback.

End with a note about implementation: "The math works — but only if you actually set things up and use them. Most SMBs buy the tools and never configure them properly. The difference between buying AI tools and getting ROI from them is execution: training, workflow setup, and follow-through. That's where a consultant earns their fee."

## Mandatory rules
- Use round numbers — precision implies false accuracy
- Keep owner's hourly rate at $75-100/hr
- No NPV, no discount rates, no sensitivity analysis, no 3-year TCO
- If uncertain, say "probably" or "depending on your volume"
- Total length: 500-700 words
```

### Embedded consulting guide material
- Property management ROI example ($215k/yr, $81k investment, 166% ROI) — from how-to-perform-ai-audits
- SMB AI stats (93%, 82%, 91%) — from smb-ai-value-playbook
- 2.7x FTE capacity gain — from smb-ai-playbook
- ROI formula — from how-to-perform-ai-audits

---

## How the "Consultant Framing" Works Across All 6 Prompts

The goal is NOT to be salesy or explicitly pitch "hire me." Instead, the prompts naturally surface the gap between knowing what to do and doing it:

- **Tech Inventory**: "Most owners don't know what AI features they already have" → implies value in someone who does
- **Pain Points**: Real ROI numbers show what's possible → the gap between current state and those numbers is where execution matters
- **Quick Wins**: Actions marked as "requires technical assistance" where appropriate → normalizes getting help
- **Roadmap**: Week-by-week plan with training touchpoints → "train people not just prompts" → someone has to do the training
- **Maturity Assessment**: Score tiers framed around execution gaps → "the gap is mostly about execution"
- **ROI Calculator**: "The math only works if you actually set things up" → the ROI case for implementation help

The cumulative effect: the owner reads the full report and thinks "this is exactly what I need — and I clearly can't do all of this myself." That's the sell, without ever saying "hire me."

---

## Verification

1. **Dry run**: `python -m strategy_factory.main run "Test Company" --dry-run` — verify pipeline still runs
2. **Live run**: Test with a real company and check:
   - Each markdown file meets its word count minimum
   - No files are truncated mid-section
   - Tables render correctly with proper headers
   - Quick wins section uses table format, not bullets
   - No "you're in a common spot" language in readiness assessment
   - No "no API required" constraint in quick wins
   - Perplexity and Claude Max appear in tool recommendations
   - Real stats and ROI numbers appear in output
   - The document as a whole leads the reader toward "I need help executing this" without explicitly pitching
3. **Word count check**: Each file should hit its target range (total ~4,300–5,700 words across all 6)
