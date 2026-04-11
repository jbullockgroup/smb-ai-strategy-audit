# Phase 2 Plan: Guide Overrides + Audience Creation Tool

**Dependency:** Phase 1 (AUDIENCE-PLAN.md) must be completed first.

## Context

Phase 1 gives us audience *selection* — a dropdown in the web app and CLI that lets users pick an audience when running an audit. Phase 2 adds two capabilities on top of that:

1. **Guide Overrides** — When an audience is selected, swap out consulting guides that don't fit with audience-specific replacements guides
2. **Audience Creation Tool** — A new "Create Audience" page in the web app that auto-generates audience files and replacement consulting guides via Perplexity research

## How Guide Overrides Work

The current system has 10 consulting guides in `Consulting Guides TLDR/`. Some are enterprise-focused and don't fit small business audiences:

- `the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era_TLDR.md` — Fortune 500 org restructuring
- `seizing-the-agentic-ai-advantage_TLDR.md` — Enterprise agentic transformation
- `kpmg-agentic-ai-advantage_TLDR.md` — Enterprise agentic AI

The audience markdown file gets a `## Guide Overrides` section listing which guides to exclude and replace. The `AudienceLoader` parses this section, and `ContextBuilder` applies the overrides when loading TLDR knowledge.

### Files to Modify

#### 1. `strategy_factory/audience_loader.py` — Add guide override methods
Add to the `AudienceLoader` class:
```python
def get_excluded_guides(self, audience_id: str) -> List[str]:
    """Parse the '### Exclude' section under '## Guide Overrides'."""

def get_replacement_guides(self, audience_id: str) -> Dict[str, str]:
    """Parse the '### Replace' section. Returns {'original.md': 'replacement.md'}"""
```
#### 2. `strategy_factory/synthesis/context_builder.py` — update `_load_tldr_knowledge`
Modify `_load_tldr_knowledge` to check for audience guide overrides:
```python
def _load_tldr_knowledge(self, deliverable_id: str, audience_id: Optional[str] = None) -> str:
    # ... existing logic to load tldr_guides from config ...

    # Apply audience overrides if audience selected
    if audience_id:
        from ..audience_loader import get_audience_loader
        loader = get_audience_loader()

        # Remove excluded guides
        excluded = loader.get_excluded_guides(audience_id)
        tldr_guides = [g for g in tldr_guides if g not in excluded]

        # Apply replacements
        replacements = loader.get_replacement_guides(audience_id)
        tldr_guides = [replacements.get(g, g) for g in tldr_guides]
```
Then pass `audience_id` through the call chain:
- `build_context()` receives it the `audience_id`
- `build_full_prompt()` passes in it `company_input.audience`

#### 3. `knowledge_base/audience/mountain_bizworks_scaleup.md` — add Guide Overrides section
Append at end of file:
```markdown
## Guide Overrides

### Exclude
- the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era_TLDR.md
- seizing-the-agentic-ai-advantage_TLDR.md
- kpmg-agentic-ai-advantage_TLDR.md

### Replace
- the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era_TLDR.md → SMB_AI_team_structure_guide.md
- seizing-the-agentic-ai-advantage_TLDR.md → SMB_quick_implementation_playbook.md
- kpmg-agentic-ai-advantage_TLDR.md → SMB_agentic_tools_for_small_teams.md
```
The replacement guides (SMB_AI_team_structure_guide.md, etc.) don **not exist yet** — they get created by the Audience Creation tool.

---

## How Audience Creation Works

A new page in the web app where the user provides a list of business names (paste or CSV upload), and the system:
1. Researches each business via Perplexity
2. Analyzes patterns across the cohort
3. Generates the audience markdown file
4. Identifies which consulting guides don't fit
5. Researches replacement guide topics via Perplexity
6. Generates new TLDR consulting guides in the same format as existing ones
7. Saves everything to the right folders

### Files to Create
#### 1. `strategy_factory/audience_creator.py` (NEW ~250 lines)
Orchestrates the audience creation pipeline:
- `create_audience(business_names, audience_name, descriptions=None)` — main entry point
- `_research_businesses(business_names, descriptions)` — Perplexity research for each business
- `_analyze_cohort(business_profiles)` — identify patterns, themes, pain points
- `_generate_audience_file(audience_name, business_profiles, cohort_analysis)` — write the audience markdown
- `_identify_guide_gaps(business_profiles)` — determine which consulting guides don't fit
- `_research_replacement_guides(gaps)` — Perplexity research for replacement topics
- `_generate_consulting_guides(replacement_topics)` — write new TLDR guides in same format as existing ones
- `get_audience_loader()` — reuse singleton from Phase 1
- `GeminiClient` — reuse existing client for content generation
- `PerplexityClient` — reuse existing client for research

#### 2. `strategy_factory/webapp.py` — add "Create Audience" page
Add 3 new routes and HTML templates:
- `GET /create-audience` — form page with text area for business names + optional CSV upload + audience name field
- `POST /create-audience/start` — starts background job, returns progress page
- `GET /create-audience/progress/<job_id>` — progress polling (same pattern as company analysis)

Progress steps shown to user:
1. "Researching business 1 of 13..."
2. "Analyzing cohort patterns..."
3. "Generating audience file..."
4. "Identifying consulting guide gaps..."
5. "Researching replacement guides..."
6. "Generating SMB consulting guides..."
7. "Complete!"

Results page shows:
- Preview of generated audience file
- List of generated replacement guides
- Download buttons for each file
- "Save to Knowledge Base" button that moves files to `knowledge_base/audience/` and `Consulting Guides TLDR/`

### Web App UI for Create Audience
Add a "Create Audience" button/card on the home page alongside the company analysis form. The page has:
- Text area: "Paste business names ( one per line or or upload CSV)"
- Optional: URL field for each business (auto-detects URLs from pasted text)
- Audience name field
- "Create Audience" button

---

## Verification
1. **Guide overrides:** Run an audit for "Spice Witch" with `mountain_bizworks_scaleup` audience → verify excluded guides are skipped and replacements are loaded
2. **Create audience:** Paste a list of 5 business names → verify all 7 pipeline steps complete → verify files saved to correct locations
3. **Backward compat:** Run audit with no audience → verify original guides load as before

## File Change Summary
| File | Action | Lines |
|------|--------|-------|
| `strategy_factory/audience_creator.py` | **NEW** | ~250 lines |
| `strategy_factory/audience_loader.py` | ADD | ~25 lines (guide override methods) |
| `strategy_factory/synthesis/context_builder.py` | MODIFY | ~15 lines (guide override logic) |
| `strategy_factory/webapp.py` | ADD | ~80 lines (create audience page) |
| `knowledge_base/audience/mountain_bizworks_scaleup.md` | ADD | ~20 lines (Guide Overrides section) |
| `Consulting Guides TLDR/SMB_*.md` | **NEW** | 3 files, generated by tool |
