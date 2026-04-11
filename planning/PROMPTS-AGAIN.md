# PROMPTS-AGAIN.md — Prompt Restructuring Plan

**Purpose**: Self-contained handoff document for a new agent session. Contains everything needed to restructure all 7 prompt files.

## Execution Order: Step 2 of 5

| Step | Plan | What it does |
|------|------|-------------|
| 1 | TLDR-FIX | Fix knowledge_loader.py (standalone, run anytime) |
| **2** | **PROMPTS-AGAIN (this plan)** | **Restructure all 7 prompt formats** |
| 3 | FIRECRAWL | Add Firecrawl infrastructure (new files, models, deps) |
| 4 | RESEARCH-ENHANCEMENTS | Merge enhancements + voice agents + pipeline wiring |
| 5 | EXEC-SUM | Add 8th deliverable (standalone after step 2) |

**Prerequisites**: None. Must complete before steps 3-5 because they add content to the restructured prompts.

## Why This Change

The current 7 prompts produce incomplete output — blank sections under headings, missing table rows, diagnostic questions listed as output instead of used for reasoning, scorecard dimensions skipped, and closing sections cut off. The root cause: the current prompts describe content in conversational prose rather than giving Gemini an explicit structural template to fill.

The old prompts (which produced complete 170-page reports without these issues) used rigid numbered sections, explicit table templates with pre-filled headers, and strict output format rules. This restructuring applies that old format to the current SMB-focused content.

**All SMB-focused content stays** — voice, tone, stats, framing devices, ROI numbers, tool recommendations, word counts. Only the structural scaffolding changes.

## The Old Format Pattern (Target)

The old prompts follow this exact structure:

```python
PROMPT = """
# Task: Generate [Descriptive Title]

Based on the [context] provided above, create [one-line description].

## Required Sections

### 1. Section Name
- instruction
- instruction

### 2. Section Name

Create a table with the following columns:
| Header | Header | Header |
|--------|--------|--------|
| [stub row 1] | [placeholder] | [placeholder] |
| [stub row 2] | [placeholder] | [placeholder] |

Categories to include:
- Item 1
- Item 2

### N. Section Name
- instructions

## Output Format
- rule
- rule
"""
```

Key characteristics:
- `# Task: Generate [Title]` — not a role description
- `Based on the [context] provided above, create [Y]` — terse opener
- `## Required Sections` — not `## What to produce`
- Numbered sections: `### 1.`, `### 2.`, etc.
- Explicit table templates with `| Header |` rows, `|---|` separators, and stub rows
- `## Output Format` — not `## Mandatory rules`

## The Current Format (To Be Replaced)

```python
PROMPT = """
You are an SMB AI strategist writing directly to a business owner.

Based on the [context], write [Y].

## What to produce

### Section Name (~X words)

Prose description of what to write...

## Mandatory rules
- rule
"""
```

## Cross-Cutting Changes (Applied to ALL 7 Files)

### A. Header transformation
Replace the role opener line with the Task format:
```
# Task: Generate [Title]

Based on the [context] provided above, create [description].
```

### B. Section header transformation
- Replace `## What to produce` with `## Required Sections`
- Number each section: `### 1.`, `### 2.`, `### 3.`, etc.
- Keep word count targets in parentheses

### C. Table template transformation
Replace prose table descriptions with explicit markdown:
- The exact `| Header | Header |` row
- The `|---|---|` separator
- Stub rows with `[placeholder]` markers
- Explicit row count instruction ("Produce this exact table with N rows")

### D. Completion enforcement rules
Add these lines to every prompt's Output Format section:
```
- Produce every section listed below in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Fill every cell in every table. No empty cells.
```

### E. Footer transformation
Replace `## Mandatory rules` with `## Output Format` and merge:
- All existing mandatory rules
- The completion enforcement rules above
- Keep the total word count target

### F. Variable name
Keep `PROMPT = """..."""` — do not change the variable name.

---

## File Locations

Files to edit (all under `strategy_factory/synthesis/prompts/`):
1. `closing.py` — "Putting It All Together"
2. `maturity_assessment.py` — "Your AI Readiness"
3. `pain_points.py` — "Where You're Losing Money"
4. `quick_wins.py` — "What To Do First"
5. `roadmap.py` — "Your Week-by-Week Plan"
6. `tech_inventory.py` — "Where You Stand Today"
7. `roi_calculator.py` — "What It Costs & What You Save"

No changes to: `__init__.py`, `config.py`, any orchestrator, `context_builder.py`, `gemini_client.py`, generation files, research files, or webapp.

---

## Per-File Implementation Details

Implementation order is by severity — worst failures first.

### 1. `closing.py` — CRITICAL

**Current problem**: Only ~77 of 400-600 words produced. 2 of 3 sections are just headings with no content.

**Current content to preserve**:
- Three-section structure (synthesis / next step / closing thought)
- 5-point synthesis instructions (biggest opportunity, tools they own, quick wins, first month, ROI math)
- Monday-morning action format
- AI Value Gap reference (88% experimenting, 5-8% capturing value)
- "Smart advisor summarizing a meeting" tone guidance
- No new recommendations rule
- Second person throughout
- 400-600 word target

**Specific changes**:
- Apply cross-cutting changes A–E above
- **Remove `{company_name}` placeholder** — the context builder does NOT replace it. Company name comes from the context header already. Just instruct Gemini to use the company name from context.
- Add to section 1: "This section MUST be a complete ~250-word narrative. Do NOT output just a heading."
- Add to section 3: "This section MUST contain a complete ~100-word paragraph. Do NOT leave it as just a heading."

**New structure should be**:
```
# Task: Generate Closing Synthesis

Based on the full AI strategy report produced above, create a clear, motivating closing section that ties everything together.

## Required Sections

### 1. What This All Means (~250 words)
[all current synthesis instructions from "What This All Means for {company_name}"]
This section MUST be a complete ~250-word narrative. Do NOT output just a heading. Write the full paragraphs.

### 2. Your One Next Step (~100 words)
[all current Monday-morning action instructions]

### 3. Closing Thought (~100 words)
[all current AI Value Gap + confidence instructions]
This section MUST contain a complete ~100-word paragraph. Do NOT leave it as just a heading.

## Output Format
- This section synthesizes — do NOT repeat details verbatim from earlier sections
- Reference earlier sections by their insights, not by section name
- No new recommendations that weren't already in the action plan or roadmap
- Write in second person ("you", "your") throughout
- No headers beyond the three listed above
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- Total length: 400-600 words
```

### 2. `maturity_assessment.py` — CRITICAL

**Current problem**: Only 3 of 5 dimensions appear in output. Scores don't add up (individual scores don't match total). Unicode arrows render as `?` in PDF.

**Current content to preserve**:
- All 5 dimension rubrics with detailed level descriptions (1-5 scale each)
- Three score tiers (5-10, 11-17, 18-25) with exact quoted text
- AI Value Gap stat (88% use AI, 5-8% capture value)
- "Organizations scoring above 70% readiness are 3x more likely to see ROI"
- AI Maturity Curve reference
- Bottom Line one-sentence format
- 600-800 word target

**Specific changes**:
- Apply cross-cutting changes A–E
- **Replace prose score instruction with explicit table template**:
```
| Dimension | Score (1-5) | Explanation |
|-----------|:-----------:|-------------|
| 1. Current AI Adoption | [1-5] | [One sentence based on research] |
| 2. Pain Awareness | [1-5] | [One sentence based on research] |
| 3. Digital Foundation | [1-5] | [One sentence based on research] |
| 4. Owner Openness | [1-5] | [One sentence based on research] |
| 5. Budget Alignment | [1-5] | [One sentence based on research] |
| **Total** | **[sum]/25** | |
```
- Add: "You MUST produce all 5 dimensions. Do not skip any dimension."
- Add: "Verify that your total equals the sum of the 5 individual scores."
- **Change Unicode arrows to text**: "Hype -> Pilot -> Habit -> Scale" instead of `→`

### 3. `pain_points.py` — HIGH

**Current problem**: Diagnostic questions (7 items) leak into output as-is instead of being used internally. "500 Customer Test" sometimes appears as just a heading with no answer.

**Current content to preserve**:
- 500 Customer Test concept and framing
- Time-wasters ranking with hours/week and dollar value at $75-100/hr
- 5 workflow analyses (Speed to Lead, Follow-Up, Database Reactivation, Internal Reporting, Document Processing) — each with What's happening now / What AI could do / Real example / Setup note
- All 5 embedded ROI numbers (dental 12%→25%, doc processing 13min/doc, webinar 4%→12%, database reactivation 2-3% = $32-48k, reporting $12k/mo)
- "Audit why before what" principle with e-commerce example
- AI Suitability Filter (structured input, predictable output, rule-based decisions, repeated)
- Content Creation Gap section
- 900-1,200 word target

**Specific changes**:
- Apply cross-cutting changes A–E
- **Rewrite 500 Customer Test with explicit template**:
```
### 1. The 500 Customer Test (~150 words)

Write this section as follows:
First, pose the thought experiment: "Imagine you woke up tomorrow with 500 new customers. What breaks first?"
Then answer it specifically for this business in 2-3 sentences naming the specific bottleneck. Write the full answer — do not leave this section as just a heading.
```
- **Change diagnostic questions framing** to prevent them from appearing in output:
```
Use these 7 diagnostic questions INTERNALLY to determine which workflows apply to this business. Do NOT output these questions — they are your reasoning framework, not your output:
1. Where's the bottleneck?
2. What breaks first under pressure?
3. What mistakes happen daily?
4. Where does time go?
5. Where's the profit opportunity?
6. Where is expertise being misused?
7. What's repeated every day?
```
- **Replace time-wasters table with explicit 5-row template**:
```
| Rank | Task | Hours/Week Lost | Dollar Value/Week |
|------|------|----------------|-------------------|
| 1 | [specific task] | [X hrs] | $[Y] |
| 2 | [specific task] | [X hrs] | $[Y] |
| 3 | [specific task] | [X hrs] | $[Y] |
| 4 | [specific task] | [X hrs] | $[Y] |
| 5 | [specific task] | [X hrs] | $[Y] |

Produce this exact table with 5 rows. Fill every cell. No empty cells.
```

### 4. `quick_wins.py` — MEDIUM-HIGH

**Current problem**: Action table sometimes has missing rows. "Biggest Opportunity" sometimes appears as just a heading.

**Current content to preserve**:
- BCG 10-20-70 rule with full context ("70% of AI success comes from people and process...")
- All 6 tool recommendations with exact prices (ChatGPT Plus $20, Claude Pro $20, Claude Max $100-200, Gemini $0-20, Perplexity $20, n8n)
- Tool preferences (use these / never recommend lists)
- Monthly investment table format
- 700-900 word target

**Specific changes**:
- Apply cross-cutting changes A–E
- Add to section 1: "Write 2-3 sentences. This MUST be a complete paragraph with specific detail. Do not output just a heading."
- **Replace action table with explicit 4-row template**:
```
| # | Action | Tool (Price) | Time to Set Up | Weekly Time Saved | What You Get | First Step Today |
|---|--------|-------------|----------------|-------------------|--------------|------------------|
| 1 | [verb-first action] | [Tool $X/mo] | [time] | [X min/day] | [outcome] | [specific thing] |
| 2 | [verb-first action] | [Tool $X/mo] | [time] | [X min/day] | [outcome] | [specific thing] |
| 3 | [verb-first action] | [Tool $X/mo] | [time] | [X min/day] | [outcome] | [specific thing] |
| 4 | [verb-first action] | [Tool $X/mo] | [time] | [X min/day] | [outcome] | [specific thing] |

Produce this exact table with 4 rows. Fill every cell. No empty cells.
```
- **Replace monthly investment table with explicit template**:
```
| Tool | Monthly Cost | What It Does | Already Paying? |
|------|-------------|--------------|-----------------|
| [Tool 1] | $X/mo | [One sentence] | [Yes/No] |
| [Tool 2] | $X/mo | [One sentence] | [Yes/No] |
| [Tool 3] | $X/mo | [One sentence] | [Yes/No] |
| **Total new cost** | **$X/mo** | | |
```
- Merge the `## Tool preferences` section into `## Output Format`

### 5. `roadmap.py` — MEDIUM

**Current problem**: "Month 3 and Beyond" section is blank.

**Current content to preserve**:
- Week 1-4 template text with specific instructions
- Consultant touchpoint language ("bring in someone who knows the tool landscape")
- Weekly Check-In with 3 questions
- "Train people not just prompts" principle
- ROI Feedback Loop (measure weekly, SMBs that track stick with AI)
- 800-1,100 word target

**Specific changes**:
- Apply cross-cutting changes A–E
- Add to Month 2: "Write 2-3 full paragraphs. Do NOT write fewer than 2 paragraphs."
- **Rewrite Month 3 and Beyond**:
```
### 3. Month 3 and Beyond (~150 words)

Write 2-3 paragraphs describing what this business looks like in 90 days when the plan is followed. Cover:
- What tools are now in daily use
- What workflows are running
- What the team is doing differently
- The direction for months 3-6

Mention that the biggest gains come in months 3-6, after the team is trained and workflows are optimized. Do NOT leave this section empty — write the full 2-3 paragraphs.
```

### 6. `tech_inventory.py` — MEDIUM

**Current problem**: "#1 AI Opportunity" section cuts off.

**Current content to preserve**:
- Shadow AI 67% stat
- "Activate what you own" principle
- AI Suitability Filter (structured input, predictable output, rule-based decisions, repeated)
- 7 tool categories with specific AI feature naming requirement
- "Based on typical [industry] businesses" fallback instruction
- 800-1,000 word target

**Specific changes**:
- Apply cross-cutting changes A–E
- **Replace tool stack table with explicit 7-row template**:
```
| Tool | What You Use It For | AI Feature Already Built In | What It Could Do For You |
|------|--------------------|-----------------------------|--------------------------|
| [Google Workspace or Microsoft 365] | [what this business uses it for] | [specific feature] | [one concrete capability] |
| [Accounting software] | [usage] | [specific AI feature] | [concrete capability] |
| [Website platform] | [usage] | [specific AI feature] | [concrete capability] |
| [Scheduling/booking tool] | [usage] | [specific AI feature] | [concrete capability] |
| [CRM or customer list] | [usage] | [specific AI feature] | [concrete capability] |
| [Industry-specific software] | [usage] | [specific AI feature] | [concrete capability] |
| [Social media / scheduling tool] | [usage] | [specific AI feature] | [concrete capability] |

Produce this exact table with 7 rows. Fill every cell. If research returns nothing about a specific tool, infer based on industry.
```
- Add to "#1 AI Opportunity": "This section MUST contain a complete 3-5 sentence paragraph. DO NOT output just a heading."

### 7. `roi_calculator.py` — LOW

**Current problem**: Works well. Only needs consistency changes.

**Specific changes**:
- Apply cross-cutting changes A–E (structural transformation only)
- Add explicit table row stubs for "Your Monthly Investment" table (3 tool rows + total row)
- Keep all other content unchanged — this is the best-performing prompt

---

## Reference: Old Prompt Examples

For structural reference, here are excerpts from the old (working) prompts at `/Volumes/JSB MEDIA/DOCUMENTS/REPOS/ai-strategy-factory-2/strategy_factory/synthesis/prompts/`:

### Old tech_inventory.py (structure pattern):
```python
PROMPT = """
# Task: Generate Technology Inventory & Data Infrastructure Assessment

Based on the company research and context provided above, create a comprehensive technology inventory document.

## Required Sections

### 1. Executive Summary
- Brief overview of current technology landscape
- Key findings and critical gaps

### 2. Current Technology Stack

Create a table with the following columns:
| Category | Tool/Platform | Purpose | AI-Ready | Data Integration |
|----------|--------------|---------|----------|------------------|

Categories to include:
- Core Business Systems (ERP, CRM, etc.)
- Communication & Collaboration
- Data & Analytics
...

### 5. AI Readiness Assessment

| Dimension | Current State | Gap | Priority |
|-----------|--------------|-----|----------|
| Data Quality | | | |
| Data Accessibility | | | |
...

## Output Format
- Use markdown formatting
- Include tables where specified
- Be specific with tool names and versions where known
- Note assumptions clearly where information is limited
"""
```

### Old maturity_assessment.py (structure pattern):
```python
PROMPT = """
# Task: Generate AI Maturity Model & Readiness Assessment

Based on the research and context provided above, create a comprehensive AI maturity assessment...

## Required Sections

### 3. Dimension-by-Dimension Analysis

Rate each dimension on a 1-5 scale:

| Dimension | Score | Evidence | Gap Analysis |
|-----------|-------|----------|--------------|
| Strategy & Vision | | | |
| Data & Infrastructure | | | |
...

#### Detailed Dimension Analysis

For each dimension, provide:

##### Strategy & Vision (X/5)
- Current state observations
- Strengths identified
...
"""
```

---

## Verification

After implementation, run the pipeline for a test company:
```bash
python -m strategy_factory.main run "Test Company" --dry-run
```

Then check each output file:

1. `01_tools_audit.md`: Tool stack table has 7 complete rows, "#1 AI Opportunity" has full paragraph
2. `02_daily_pain_points.md`: "500 Customer Test" has thought experiment + answer, diagnostic questions NOT in output, time-wasters table has 5 rows
3. `03_action_plan.md`: Action table has 4-5 consecutive rows, "Biggest Opportunity" has content
4. `04_simple_roadmap.md`: "Month 2" and "Month 3" both have 2+ paragraphs
5. `05_readiness_assessment.md`: All 5 dimensions present, total equals sum, no Unicode arrows
6. `06_roi_snapshot.md`: No regressions
7. `07_closing.md`: All 3 sections have content, word count 400-600
