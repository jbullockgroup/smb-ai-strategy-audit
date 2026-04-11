# AUDIENCE-PLAN.md — Audience Knowledge Integration for AI Strategy Factory

## Background & Context

The user (Jeff) is consulting for **Mountain BizWorks' ScaleUp WNC program** — a cohort-based growth strategy program for small businesses in Western North Carolina. He needs to generate AI strategy deliverables for each of the 13 businesses in **Cohort 14**, but the current system produces generic enterprise-style output that doesn't fit these businesses (artisans, food makers, cleaning companies, yarn shops, etc. with $150K–$2.5M revenue).

## What We're Building

An **audience system** that lets the user select an audience when running a company analysis. When selected, all 15 strategy deliverables are automatically tailored for that audience — different tone, different research, different recommendations.

**Key design principle:** Adding a new audience = creating one markdown file and dropping it in a folder. No code changes.

## What Already Exists

A knowledge base file is already created at:
```
knowledge_base/audience/mountain_bizworks_scaleup.md
```
This file contains:
- Organization profile (Mountain BizWorks)
- 13 business profiles with industry, location, growth vectors
- Cohort analysis (themes, pain points, common characteristics)
- AI Strategy Relevance section
- **Tone Guidance** section (7 guidelines for how to write)
- **Research Queries** section (6 supplemental Perplexity queries)

Do NOT modify this file. It's complete.

## How It Should Work (User Flow)

### Web App
1. User enters business name (e.g., "Spice Witch")
2. User adds context (e.g., "seed oil-free chili oils, Asheville-based")
3. User uploads logo
4. User selects audience from dropdown (e.g., "Mountain BizWorks ScaleUp WNC")
5. Dropdown is auto-populated from files in `knowledge_base/audience/`
6. User hits "Start Analysis"
7. All 15 deliverables come out tailored for WNC small businesses

### CLI
```bash
python -m strategy_factory.main run "Spice Witch" --audience mountain_bizworks_scaleup --mode quick
```

### When no audience is selected
Pipeline runs exactly as it does today — generic enterprise output. Zero changes.

---

## Implementation Plan

### Step 1: Create `strategy_factory/audience_loader.py` (NEW FILE)

Follow the pattern from `strategy_factory/knowledge_loader.py` (read that file for reference — same caching, same singleton pattern).

```python
class AudienceLoader:
    def __init__(self, audience_dir: Path):
        # audience_dir defaults to PROJECT_ROOT / "knowledge_base" / "audience"
        # Cache and available_audiences list

    @property
    def available_audiences(self) -> List[Dict[str, str]]:
        # Scan audience_dir for *.md files
        # Return [{"id": "mountain_bizworks_scaleup", "name": "Mountain BizWorks ScaleUp WNC"}]
        # "name" comes from the # H1 heading in each file
        # "id" is the filename stem

    def load_audience(self, audience_id: str) -> Optional[str]:
        # Load {audience_id}.md, return full markdown string, cache it
        # Return None if file doesn't exist

    def get_section(self, audience_id: str, section_name: str) -> str:
        # Extract everything between "## {section_name}" and the next "## " heading
        # Use regex: r"^##\s+" + section_name + r"\s*\n(.*?)(?=\n##\s|\Z)"
        # Return empty string if section not found

    def get_tone_guidance(self, audience_id: str) -> str:
        # Convenience: self.get_section(audience_id, "Tone Guidance")

    def get_research_queries(self, audience_id: str) -> List[str]:
        # Parse the "## Research Queries" section
        # Extract each line starting with "- " (bullet list items)
        # Strip the "- " prefix, return as list of strings
        # Replace {current_year} with actual current year

# Module-level singleton
_loader_instance = None
def get_audience_loader() -> AudienceLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = AudienceLoader()
    return _loader_instance
```

The `AUDIENCE_DIR` constant should be `PROJECT_ROOT / "knowledge_base" / "audience"`. Import `PROJECT_ROOT` from config.

---

### Step 2: Add `audience` field to `CompanyInput` in `models.py`

**File:** `strategy_factory/models.py`
**Location:** Line 70, after `logo_path: Optional[str] = None`

Add ONE line:
```python
    audience: Optional[str] = Field(default=None, description="Audience ID for tailored output")
```

This defaults to `None` so all existing code works unchanged. `PipelineState` stores `CompanyInput`, so the audience selection is automatically persisted in `state.json` for resume operations.

---

### Step 3: Wire audience into `ContextBuilder`

**File:** `strategy_factory/synthesis/context_builder.py`

**3a.** Add import at top (after line 14):
```python
from ..audience_loader import AudienceLoader
```

**3b.** Add `audience_loader` to `__init__` (line 29-43):
Add parameter: `audience_loader: Optional[AudienceLoader] = None`
Add assignment: `self.audience_loader = audience_loader or AudienceLoader()`
Add cache: `self._audience_context: Optional[str] = None`

**3c.** Add method `_load_audience_context`:
```python
def _load_audience_context(self, audience_id: Optional[str]) -> str:
    if not audience_id:
        return ""
    if self._audience_context is not None:
        return self._audience_context
    content = self.audience_loader.load_audience(audience_id)
    if content:
        self._audience_context = (
            f"## Audience Context: {audience_id}\n\n"
            f"The strategy should be tailored for the following audience:\n\n"
            f"{content}"
        )
        return self._audience_context
    return ""
```

**3d.** In `build_context()` (line 64-93), add to the returned dict (after `confidence_scores` at line 90):
```python
"audience_context": self._load_audience_context(company_input.audience),
```

**3e.** In `build_full_prompt()` (line 308-365), after the TLDR knowledge block (after line 348), add:
```python
# Add audience context
if context.get("audience_context"):
    prompt_parts.append(f"\n{context['audience_context']}")
```

This positions audience knowledge after consulting guides but before dependencies and the prompt template. Gemini sees the full audience context for every deliverable.

---

### Step 4: Add audience tone override to system instructions

**File:** `strategy_factory/synthesis/orchestrator.py`

**4a.** Change `_get_system_instruction` signature (line 224):
```python
def _get_system_instruction(self, deliverable_id: str, audience_id: Optional[str] = None) -> str:
```

**4b.** After the `base_instruction` string (before `return base_instruction` at line 238), add:
```python
if audience_id:
    from ..audience_loader import get_audience_loader
    loader = get_audience_loader()
    tone = loader.get_tone_guidance(audience_id)
    if tone:
        base_instruction += f"\n\n## Audience-Specific Tone Guidance\n\n{tone}"
return base_instruction
```

**4c.** In `_generate_deliverable` (line 202-204), change the system_instruction call:
```python
system_instruction=self._get_system_instruction(
    deliverable_id,
    audience_id=company_input.audience,
),
```

This works because `_generate_deliverable` already receives `company_input` which now has the `audience` field.

---

### Step 5: Add audience supplemental research queries

**File:** `strategy_factory/research/orchestrator.py`

**5a.** In the `research` method (line 104-176), after Phase 6 (line 160) and before "Build final output" (line 163), add:
```python
# Phase 7: Audience-specific supplemental queries
if company_input.audience:
    self._report_progress("audience_supplemental", 0.88)
    self._execute_audience_queries(company_input.audience, industry)
```

**5b.** Add new method to the class:
```python
def _execute_audience_queries(self, audience_id: str, industry: str) -> None:
    """Execute audience-specific supplemental research queries."""
    from ..audience_loader import get_audience_loader

    loader = get_audience_loader()
    queries = loader.get_research_queries(audience_id)

    for i, query in enumerate(queries):
        # Inject industry context into query
        full_query = f"{query} {industry}" if industry else query

        result = self.client.search(
            query=full_query,
            max_results=5,
            search_recency_filter="month",
            model="sonar",
        )

        # Store with prefixed key so result_processor picks it up
        self.results[f"audience_{audience_id}_{i}"] = result

        self._report_progress(
            f"audience_supplemental: query {i+1}/{len(queries)}", None
        )
```

---

### Step 6: Add `--audience` flag to CLI

**File:** `strategy_factory/main.py`

**6a.** Add argument to run subparser (after `--verbose` at line 140):
```python
run_parser.add_argument(
    "--audience", "-a",
    type=str,
    default=None,
    help="Audience ID for tailored output (e.g., 'mountain_bizworks_scaleup')",
)
```

**6b.** Pass audience into CompanyInput (around line 239):
```python
company_input = CompanyInput(
    name=company_name,
    context=args.context,
    mode=mode,
    industry=args.industry or None,
    audience=args.audience or None,  # NEW
)
```

**6c.** Display audience in header (after line 227):
```python
if args.audience:
    print(f"Audience: {args.audience}")
```

---

### Step 7: Add audience dropdown to web app

**File:** `strategy_factory/webapp.py`

**7a.** In the form HTML (around line 788, after the Research Mode radio group div and before the submit button), add a new form group:
```html
<div class="form-group">
    <label for="audience">Audience (optional)</label>
    <select id="audience" name="audience" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px;">
        <option value="">General (no audience tailoring)</option>
        {% for aud in audiences %}
        <option value="{{ aud.id }}">{{ aud.name }}</option>
        {% endfor %}
    </select>
    <small style="color: #666; display: block; margin-top: 4px;">
        Select an audience to tailor deliverables for a specific program or cohort
    </small>
</div>
```

**7b.** The HOME_CONTENT template uses Jinja2. Update the home route to pass available audiences. Find where the home page renders (the function that renders `HOME_CONTENT`) and add audience data:
```python
from strategy_factory.audience_loader import get_audience_loader
audiences = get_audience_loader().available_audiences
# Pass 'audiences=audiences' to the template render
```

**7c.** In `start_analysis` route (line 1071), extract audience:
```python
audience = request.form.get('audience', '').strip() or None
```

Store in active_jobs:
```python
active_jobs[job_id] = {
    ...existing fields...
    "audience": audience,  # NEW
}
```

**7d.** Update thread call (line 1120-1122) to pass audience:
```python
thread = threading.Thread(
    target=run_pipeline,
    args=(job_id, company_name, context, mode, logo_path_str, audience),
    daemon=True
)
```

**7e.** Update `run_pipeline` function signature (line 1458):
```python
def run_pipeline(job_id: str, company_name: str, context: str, mode: str, logo_path: str = None, audience: str = None):
```

**7f.** In `run_pipeline`, add audience to CompanyInput creation (line 1473-1478):
```python
company_input = CompanyInput(
    name=company_name,
    context=context,
    mode=research_mode,
    logo_path=logo_path,
    audience=audience,  # NEW
)
```

---

## Verification Steps

1. **Backward compatibility:** Run `python -m strategy_factory.main run "Test Company" --dry-run` — should work with zero errors, no audience-related output
2. **With audience:** Run `python -m strategy_factory.main run "Spice Witch" --audience mountain_bizworks_scaleup --context "Specialty condiment company in Asheville NC" --mode quick` — verify supplemental queries execute and output is tailored
3. **Web app:** Start with `python -m strategy_factory.webapp`, verify dropdown appears with "Mountain BizWorks ScaleUp WNC" option, run a test
4. **Resume:** Verify `state.json` preserves audience field and resume works

## File Change Summary

| File | Action | Lines Changed |
|------|--------|---------------|
| `strategy_factory/audience_loader.py` | **NEW** | ~100 lines |
| `strategy_factory/models.py` | ADD 1 line | Line ~70 |
| `strategy_factory/synthesis/context_builder.py` | ADD ~25 lines | Import, init, method, 2 insertions |
| `strategy_factory/synthesis/orchestrator.py` | ADD ~10 lines | Param + tone logic in 2 methods |
| `strategy_factory/research/orchestrator.py` | ADD ~20 lines | Phase 7 block + new method |
| `strategy_factory/main.py` | ADD ~5 lines | Argument, field, display |
| `strategy_factory/webapp.py` | ADD ~15 lines | Form field, extraction, pipeline wiring |

**Total:** ~190 lines of new code. **0 lines removed from any file.**

## Key Design Decisions

1. **All audience data lives in the markdown file** — tone guidance, research queries, business profiles, everything. No config.py entries needed for new audiences.
2. **Audience context is injected at the ContextBuilder level** — affects all 15 deliverables without editing 15 prompt templates.
3. **Tone override goes in system instructions** — stronger influence on Gemini's writing style than user prompt content.
4. **Audience defaults to None everywhere** — full backward compatibility. When None is selected, pipeline is identical to today.

## Reference Files to Read Before Starting

- `strategy_factory/knowledge_loader.py` — Pattern to follow for AudienceLoader
- `strategy_factory/models.py` — CompanyInput model (line 56-71)
- `strategy_factory/synthesis/context_builder.py` — Where audience context gets injected
- `strategy_factory/synthesis/orchestrator.py` — System instructions (line 224-238)
- `strategy_factory/research/orchestrator.py` — Research phases (line 104-176)
- `strategy_factory/main.py` — CLI run command (line 213-244)
- `strategy_factory/webapp.py` — Form HTML (~line 780-793), start_analysis route (line 1071), run_pipeline (line 1458)
- `knowledge_base/audience/mountain_bizworks_scaleup.md` — The existing audience file (DO NOT MODIFY)
