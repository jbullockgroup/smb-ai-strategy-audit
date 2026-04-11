# Prompt Gaps Analysis: Current Prompts vs. New Consulting Guides

Investigation report — 2026-04-04

---

## Summary

The new consulting guides have **substantial material** that can make every prompt more robust. The current prompts are structurally sound but thin on evidence — they ask Gemini to produce content based on company research alone, without injecting authoritative data, frameworks, or real examples. The new guides fix exactly that gap.

---

## Prompt-by-Prompt Breakdown

### 1. `tech_inventory.py` — "Where You Stand Today"

**Current state:** Generic list of tool categories (Google Workspace, QuickBooks, etc.) with a vague instruction to "describe 1-2 AI features that are already built in."

**What the new guides add:**
- **`ai-smb-gws.md`** — Specific Gemini-in-Workspace features by area (Help me write in Docs, Help me organize in Sheets, Gemini in Gmail sidebar). Concrete feature-level detail the prompt currently lacks.
- **`guide-for-smb-leaders.md`** — 4 stages of AI maturity with security implications per stage (free tools = data leakage risk, paid = fragmented security). Could make the opportunity map sharper.
- **`built-500-ai-workflows.md`** — The "activate existing tools before buying new" principle with specifics (Microsoft 365, QuickBooks, Shopify Magic). Also the diagnostic: "You don't need new tools, you need to turn on what you already have."
- **`smb-ai-playbook.md`** — Shadow AI statistic (67% of businesses have it, 41% data risks) and the "Kill Shadow AI" Week 1 action (Chrome extension audit, centralize to 1-2 platforms).

**Verdict:** The prompt can be significantly beefed up by injecting specific features per tool, the "activate what you own" principle, and the shadow AI audit angle.

---

### 2. `pain_points.py` — "Where You're Losing Money"

**Current state:** Already uses the "500 Customer Test" from `built-500-ai-workflows`. Has 5 workflows but they're described generically. Content Creation Gap is a thin one-paragraph ask.

**What the new guides add:**
- **`built-500-ai-workflows.md`** — Real ROI numbers for each workflow: dental clinic speed-to-lead (12%→25%), document processing ($70k/yr savings), follow-up sequences ($36k→$90k per webinar), database reactivation ($32-48k recovered), internal reporting ($12k/mo error reduction). The current prompt has none of these examples.
- **`how-to-perform-ai-audits.md`** — The 6-step audit framework with atomic task breakdown and AI Suitability Filter (4 YES = automatable). The ROI calculation formula: `(time waste × people × days × loaded $/hr) + lost revenue`.
- **`7-workflow-questions-for-ai-success.md`** — 7 diagnostic questions per area (bottleneck, break points, mistakes, time waste, profit opportunity, expert misuse, daily repetition). These are better structured than the current generic list.
- **`what-an-ai-audit-really-is.md`** — "Audit why before what" principle. The e-commerce example (thought they needed AI writer, actually needed integration → 8hrs/wk saved at $0 cost). Tool fatigue insight (client wasting 70% of 5 AI tools).

**Verdict:** This prompt is already using the "500 customer test" framing from the guides, but it's missing the **hard ROI numbers**, the **7 diagnostic questions**, and the **real examples** that would make each workflow feel concrete and specific rather than generic.

---

### 3. `quick_wins.py` — "What To Do First"

**Current state:** Good structure (3-5 actions, tool preferences, budget cap). But tool recommendations are thin — just names and prices, no guidance on *when* to recommend what.

**What the new guides add:**
- **`30-day-ai-pilot.md`** — Complete 4-week pilot structure with daily actions (Week 1: Identify & Score, Week 2: Select & Setup, Week 3: Test & Adjust, Week 4: Decide & Plan). Budget tiers: Starter ($200-500), Standard ($500-1k), Advanced ($1-2k). ROI calculation formula with example (chatbot $1.8k/yr saves $16.6k = 469% ROI).
- **`90-day-ai-playbook.md`** — 6-step process with specific Week 1 actions (activate existing tools, no new buys). The "train people not just prompts" 15-minute weekly check-in cadence.
- **`smb-ai-value-playbook.md`** — The workflow redesign principle (McKinsey's biggest-impact finding): "If I were building this process from scratch with AI available, what would it look like?" Also the BCG 10-20-70 rule and the "SMB Speed Advantage" (redesign in an afternoon vs 12-month enterprise programs).
- **`smb-ai-playbook.md`** — Scale playbook: 1 hero use case per function, document ROI weekly, train 1 power user per workflow, expand only after 4-week positive ROI. The 80/15/5 resource allocation rule.

**Verdict:** Strong material for making the actions more structured and evidence-based. The current prompt's tool preference section could be updated with the "activate existing tools first" principle and the specific pilot methodology.

---

### 4. `roadmap.py` — "Your Week-by-Week Plan"

**Current state:** 4-week first month, then 2 paragraphs for Month 2 and Month 3. Very thin — just "name specific tools."

**What the new guides add:**
- **`30-day-ai-pilot.md`** — Full 30-day checklist with specific daily tasks for each week. This is essentially a more detailed version of what the prompt is already trying to produce.
- **`90-day-ai-playbook.md`** — The complete 90-day framework (choose one problem → activate tools → measure → protect data → train people → review & scale). This maps perfectly to the Month 1-3 structure.
- **`smb-ai-playbook.md`** — Week 1-4 (Kill Shadow AI), Week 5-12 (Build AI Habits by function: Marketing, Delivery, Finance), then Scale Playbook (4-step cycle).
- **`ai-implementation-steps-smb.md`** — 13-step model with phase benchmarks (Planning: 4-8 weeks, Data Prep: 8-16 weeks, Pilots: 12 weeks, Scale: 6-12 months). Statistics on failure rates (73% abandon after pilot, 82% longer than planned).

**Verdict:** This is the prompt with the **biggest gap** between current state and available material. The current version is ~350 words of vague guidance. The guides provide a complete week-by-week methodology that could make this section dramatically more actionable.

---

### 5. `maturity_assessment.py` — "Your AI Readiness"

**Current state:** 5 questions scored 0-3 (total /15). Per the resolution outline, this should change to 1-5 scoring (total /25).

**What the new guides add:**
- **`ai-readiness-score.md`** — A formal 5-dimension readiness framework with weights: Data Maturity (30%), Process Documentation (20%), Team Capability (25%), Infrastructure (15%), Budget Alignment (10%). Scoring 0-100 with benchmarks (0-40: build foundations, 41-60: emerging, 61-80: strong, 81-100: leader). Statistics: orgs scoring >70% are 3x more likely to succeed within 12 months.
- **`guide-for-smb-leaders.md`** — 4 stages of AI maturity with concrete indicators per stage and 7 quick assessment actions (survey team, review subscriptions, audit extensions, etc.).
- **`smb-ai-playbook.md`** — AI Maturity Curve (Hype → Pilot → Habit → Scale) with statistics (73% experimenting, 19% scaling, 8% AI-first).
- **`ai-governance-smb.md`** — 7-step governance framework with proportionate principles for SMEs.

**Verdict:** The current scoring dimensions are reasonable for SMBs but lack the sophistication of the 5-dimension weighted framework. The 1-5 scoring upgrade from the resolution outline aligns with the readiness score guide's approach. The benchmark statistics (3x success rate for >70% scores) would make the "What Your Score Means" section much more credible.

---

### 6. `roi_calculator.py` — "What It Costs & What You Save"

**Current state:** Simple table + break-even calc + "the real calculation" paragraph. Uses $75-100/hr owner rate.

**What the new guides add:**
- **`how-to-perform-ai-audits.md`** — Concrete ROI formula with real example: property management ($215k/yr impact: lead response +$161k, tenant comms -$42k saved, maintenance -$12.5k saved). Investment: $81k = 166% Year 1 ROI, 9-month payback.
- **`built-500-ai-workflows.md`** — Per-workflow ROI data: Speed-to-lead (dental: same $5k/mo ads, +13 patients), Document processing (45 hrs/wk freed, $70k+ savings), Follow-up ($36k→$90k per webinar), Database reactivation ($32-48k recovered, no new ads), Internal reporting (45min/day + $12k/mo error cuts).
- **`30-day-ai-pilot.md`** — Budget tiers (Starter $200-500, Standard $500-1k, Advanced $1-2k) with ROI expectations (200-400%). The ROI calculation example: (hrs saved/wk × rate × 52) - (tool + setup).
- **`smb-ai-value-playbook.md`** — SMB AI stats: 93% using AI to scale reported revenue growth (41% saw >10% gains), 82% reported cost reductions, 91% saw YoY ROI.
- **`smb-ai-playbook.md`** — ROI Feedback Loop principle (weekly measurement prevents drift), the 2.7x effective FTE capacity gain stat.

**Verdict:** The current ROI prompt is honest but thin. The guides provide real-dollar examples and formulas that would make the math section feel credible rather than made up.

---

## Cross-Cutting Themes from the Guides

Several ideas appear across multiple guides that could strengthen *all* prompts:

1. **"Activate existing tools first"** — appears in `90-day-ai-playbook`, `built-500-ai-workflows`, `ai-smb-gws`, `guide-for-smb-leaders`. Currently only weakly referenced in `tech_inventory.py`.

2. **The AI Value Gap** (88% use AI, only 5-8% capture value) — from `smb-ai-value-playbook`. This is a powerful framing statistic for the whole report.

3. **BCG's 10-20-70 Rule** (70% people/process, 20% tech, 10% algorithms) — from `smb-ai-value-playbook`. Undermines the "just buy tools" mentality.

4. **Workflow Redesign vs. Bolting On** — McKinsey's finding that redesigning processes from scratch has the biggest impact. Currently absent from all prompts.

5. **Shadow AI** (67% of businesses have it) — from `smb-ai-playbook` and `guide-for-smb-leaders`. Relevant to tech_inventory and maturity_assessment.

6. **The "pipe" metaphor** — from `built-500-ai-workflows`: fix the clog before pouring more water. Great for pain_points or the new closing section.

---

## Priority Ranking (Biggest Impact)

| Rank | Prompt | Gap Size | Why |
|------|--------|----------|-----|
| 1 | `roadmap.py` | Largest | Currently ~350 words of vague guidance; guides provide complete week-by-week methodology |
| 2 | `pain_points.py` | Large | Missing hard ROI numbers, 7 diagnostic questions, and real industry examples |
| 3 | `maturity_assessment.py` | Structural | Needs 1-5 scoring upgrade + weighted dimensions + benchmark statistics |
| 4 | `roi_calculator.py` | Medium | Has structure but lacks real-dollar examples and credible formulas |
| 5 | `quick_wins.py` | Medium | Good structure but needs pilot methodology and "activate existing first" principle |
| 6 | `tech_inventory.py` | Medium | Needs specific feature-level detail and shadow AI audit angle |
