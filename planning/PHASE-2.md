# Plan: Restructure Synthesis Prompts for Consistent Output

## Context

The current synthesis prompts produce inconsistent, often truncated output. The investigation (PHASE-2-PROMPT-STRUCTURE.md) found that the root cause is conversational prompt style triggering excessive thinking tokens in Gemini 2.5 Flash, leaving little budget for actual output. The old enterprise-style prompts with explicit schemas produced 13x more content. This plan rewrites all 6 prompts with structural scaffolding, adds a closing section, and fixes the token limit safety net.

## Total word count target: ~5,500-6,500 words across 7 sections (18-20 pages in final DOCX)

---

## Part 1: Create Prompt Template Pattern

Every prompt will follow this structure:

```
## Role
One line establishing who's writing and for whom.

## What to produce

### Section Name (WORD COUNT TARGET)
- Explicit instruction of what goes here
- Specific table schemas with column names where tables are needed
- Named items to include (not "list some tools" but "include these categories: X, Y, Z")
- Embedded stats/examples to use

### Next Section Name (WORD COUNT TARGET)
...

## Mandatory rules
- Every section must end with a complete sentence.
- Never truncate mid-table or mid-section.
- If you run out of research data for a specific item, say so plainly rather than skipping it.
- Total length: MIN-MAX words
```

Key differences from current prompts:
- Per-section word budgets instead of a single total
- Explicit table schemas with column headers
- Named categories/items instead of "include relevant ones"
- Stats and examples embedded directly in the prompt
- Completeness instructions as mandatory rules

---

## Part 2: Rewrite All 6 Prompts

### File: `strategy_factory/synthesis/prompts/tech_inventory.py`

**Target: 800-1,000 words**

Section structure:
1. **Your Current Tool Stack** (~350 words) — Table with columns: `Tool | What You Use It For | AI Feature Already Built In | What It Could Do For You`. Rows for: Google Workspace/Microsoft 365 (with specific features: Help me write, Gemini sidebar, Smart Compose), accounting software, website platform, scheduling tool, CRM/customer list, industry-specific software, social media. Embed: "67% of SMBs have shadow AI — tools employees use without approval" stat. Include fallback instruction: if research returns nothing about tools, infer based on industry and size.
2. **What's Still Manual** (~250 words) — 6-8 bullet items. Format: `Task — Time it takes — What AI does instead`. Specific to their industry.
3. **Your #1 AI Opportunity** (~150 words) — 3-5 sentence paragraph identifying the single biggest opportunity. Ends with one declarative sentence.

Embedded material:
- Shadow AI stat (67%, from smb-ai-playbook)
- "Activate what you already own before buying new" principle (from built-500-ai-workflows)
- Specific Google Workspace AI features (from ai-smb-gws)
- Cowork mention: "If you want a tool that can audit your own files and do multi-step work autonomously, consider Claude Cowork ($100-200/mo on Max plan)"

### File: `strategy_factory/synthesis/prompts/pain_points.py`

**Target: 900-1,200 words**

Section structure:
1. **The 500 Customer Test** (~150 words) — Same framing, answer specifically for this business.
2. **Your Time-Wasters Ranked** (~200 words) — Top 5 list with hours/week and dollar value at $75-100/hr.
3. **Your Highest-Impact Workflows** (~400 words) — Renamed from "5 Boring Workflows." For each of the 5 that applies: Speed to Lead, Follow-Up Sequences, Database Reactivation, Internal Reporting, Document Processing. Each gets a mini-structure: What's happening now → What AI could do → Real-world example. Embed real ROI numbers: dental speed-to-lead (12%→25%), document processing ($70k/yr), follow-up ($36k→$90k), database reactivation ($32-48k), reporting ($12k/mo error reduction).
4. **The Content Creation Gap** (~200 words) — Expanded from one paragraph to a full subsection. Where they're falling short (social, email, blog, reviews), opportunity cost, and why this is an easy win with AI.

Embedded material:
- Real ROI numbers from built-500-ai-workflows
- 7 diagnostic questions as framing (from 7-workflow-questions)
- ROI formula: `(time waste × people × days × loaded $/hr) + lost revenue` (from how-to-perform-ai-audits)
- "Audit why before what" principle (from what-an-ai-audit-really-is)

### File: `strategy_factory/synthesis/prompts/quick_wins.py`

**Target: 700-900 words**

Section structure:
1. **Your Biggest Opportunity Right Now** (~100 words) — 2-3 sentences identifying the #1 opportunity.
2. **Your Top Actions This Month** (~400 words) — 3-5 actions, each with: What to do, Tool (name + price), Time investment, What you get, First step right now.
3. **Tool Recommendations** (~150 words) — Updated tool preferences section. Add Claude Cowork for owners who want autonomous multi-step work ($100-200/mo Max plan). Keep ChatGPT Plus, Claude Pro, Gemini. Keep n8n for automation. Update "never recommend" list.
4. **Total Monthly Investment** (~100 words) — Simple table: Tool | Monthly Cost | What It Does. Total under $150/mo.

Embedded material:
- "Activate existing tools first" principle (from 90-day-ai-playbook)
- Budget tiers: Starter ($200-500), Standard ($500-1k) — from 30-day-ai-pilot (adapted for monthly tool spend, not pilot budget)
- Cowork as recommended tool for non-technical SMB owners

### File: `strategy_factory/synthesis/prompts/roadmap.py`

**Target: 800-1,100 words**

Section structure:
1. **Your First 30 Days** (~400 words) — 4 weeks, 2-3 tasks per week. Each task has: action, specific tool, time estimate. Week 1: Activate existing tools + audit shadow AI. Week 2: Set up first AI tool. Week 3: Build first workflow. Week 4: Measure and adjust. Embed Cowork in Week 2-3 as option for owners who want autonomous help.
2. **Month 2: Build on What's Working** (~200 words) — 2-3 paragraphs. What to add once basics are running. Name tools.
3. **Month 3 and Beyond** (~150 words) — What the business looks like in 90 days. Direction, not predictions.
4. **Your Weekly Check-In** (~100 words) — NEW. The 15-minute weekly cadence: What did I use AI for? What saved time? What should I try next? From 90-day-ai-playbook's "train people not just prompts."

Embedded material:
- 30-day pilot structure from 30-day-ai-pilot
- 90-day framework from 90-day-ai-playbook
- "Train people not just prompts" weekly check-in
- 80/15/5 resource allocation rule from smb-ai-playbook

### File: `strategy_factory/synthesis/prompts/maturity_assessment.py`

**Target: 600-800 words**

Section structure:
1. **Where You Stand** (~100 words) — 3-4 sentence narrative placing the business in context.
2. **Your Readiness Scorecard** (~350 words) — 5 questions, each scored 1-5 (total /25). Explicit rubric for each level. Changed from 0-3 per the resolution outline.
   - Current AI Adoption (1-5)
   - Pain Awareness (1-5)
   - Digital Foundation (1-5)
   - Owner Openness (1-5)
   - Budget Alignment (1-5)
3. **What Your Score Means** (~150 words) — Score tiers recalibrated for /25: 5-10 Not Ready Yet, 11-17 Ready to Start, 18-25 Ready to Scale. Embed stat: "Organizations scoring >70% are 3x more likely to succeed within 12 months."
4. **Bottom Line** (~50 words) — One sentence summary with the business name and score.

Embedded material:
- 5-dimension weighted framework concept from ai-readiness-score (simplified for SMB)
- "3x success rate for >70% scores" stat
- AI Maturity Curve (Hype → Pilot → Habit → Scale) from smb-ai-playbook

### File: `strategy_factory/synthesis/prompts/roi_calculator.py`

**Target: 500-700 words**

Section structure:
1. **Your Monthly Investment** (~100 words) — Table: Tool | Monthly Cost | What It Does | Note if already paying.
2. **What You Get Back** (~250 words) — For each time-saving: task, hours saved/week, dollar value at $75-100/hr. Embed SMB AI stats: 93% using AI to scale reported revenue growth, 82% cost reductions, 91% YoY ROI.
3. **When You Break Even** (~100 words) — Simple statement with timeframe.
4. **The Real Calculation** (~150 words) — Honest paragraph putting it together with a ratio. Embed ROI formula: `(hrs saved/wk × rate × 52) - (tool + setup)`.

Embedded material:
- Real-dollar property management example: $215k/yr impact, $81k investment, 166% ROI, 9-month payback (from how-to-perform-ai-audits)
- SMB AI stats from smb-ai-value-playbook
- 2.7x effective FTE capacity gain from smb-ai-playbook

---

## Part 3: Update Configuration

### File: `strategy_factory/config.py`
- Add `07_closing` to DELIVERABLES dict with name "Putting It All Together", format "markdown", dependencies: ALL markdown deliverables

### File: `strategy_factory/synthesis/prompts/__init__.py`
- Import CLOSING_PROMPT from closing.py
- Add to PROMPTS dict: `"07_closing": CLOSING_PROMPT`

### File: `strategy_factory/synthesis/orchestrator.py`
- Add `07_closing` to GENERATION_ORDER as a new level after the existing 3 levels
- Update system instruction to include Claude Cowork reference and 2026 tool landscape

---

## Part 5: Fix Token Limits & Truncation Detection

### File: `strategy_factory/synthesis/gemini_client.py`
- Change `max_output_tokens` default from 8192 to 32768 (line 99)
- After `response = model.generate_content(...)` (line ~146), check `response.candidates[0].finish_reason`
- If `finish_reason == MAX_TOKENS`: log a warning and flag the result as potentially truncated
- Add a `truncated` field to the generation result model

---

## Verification

1. **Dry run**: `python -m strategy_factory.main run "Test Company" --dry-run` — verify pipeline runs with new prompt structure
2. **Live run**: Test with a real company and check:
   - Each markdown file meets its word count minimum
   - No files are truncated mid-section
   - Tables render correctly with proper headers
   - Closing section appears and references the other sections
   - Final DOCX compiles and hits 15-20 pages
3. **Truncation check**: Verify that if a response hits MAX_TOKENS, the system logs a warning instead of silently accepting truncated output
