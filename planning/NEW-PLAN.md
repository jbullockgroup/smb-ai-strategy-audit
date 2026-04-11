# Revised Plan: Audience System + Guide Overrides

## Context

The current AUDIENCE-PLAN.md and GUIDE-OVERRIDES.md have structural issues: redundant context injection, a contradictory Exclude/Replace model, two unrelated features bundled in one plan, and a conflict about whether `mountain_bizworks_scaleup.md` can be modified. This revision fixes those issues and splits the work into three clean phases.

---

## Phase 1: Audience Selection (revised AUDIENCE-PLAN.md)

### Changes from original plan

1. **Drop `audience_context` from `build_context()` dict.** The original plan adds it to the dict AND injects it in `build_full_prompt()`, but nothing else reads the dict entry. Inject directly in `build_full_prompt()` only.
2. **Pre-thread `audience_id` into `_load_tldr_knowledge()` now** (pass-through, unused until Phase 2A) so guide overrides don't require a second round of changes to context_builder.py.
3. **Smarter research query templating.** Don't blindly append `{industry}` to every query. Instead, support `{industry}` and `{current_year}` as template variables that queries can optionally include. Queries that don't use `{industry}` won't get it forced on them.
4. **Acknowledge deliberate double tone injection.** The full audience markdown (including Tone Guidance) goes into the user prompt, AND tone guidance is extracted separately into Gemini's system instruction. This is intentional — system instructions have stronger influence on writing style. Add a code comment noting this.
5. **Remove "Do NOT modify this file" from the audience file instruction.** Phase 2A needs to add a Guide Overrides section to it.

### Step 1: Create `strategy_factory/audience_loader.py` (NEW)

Follow `strategy_factory/knowledge_loader.py` pattern (singleton, caching).

```python
class AudienceLoader:
    def __init__(self, audience_dir: Path = None):
        # Default: PROJECT_ROOT / "knowledge_base" / "audience"

    @property
    def available_audiences(self) -> List[Dict[str, str]]:
        # Scan *.md files, return [{"id": stem, "name": H1 heading}]

    def load_audience(self, audience_id: str) -> Optional[str]:
        # Load full markdown, cache it

    def get_section(self, audience_id: str, section_name: str) -> str:
        # Extract between "## {section_name}" and next "## " or EOF

    def get_tone_guidance(self, audience_id: str) -> str:
        # Convenience: get_section("Tone Guidance")

    def get_research_queries(self, audience_id: str) -> List[str]:
        # Parse "## Research Queries" bullet items
        # Replace {current_year} with actual year
        # Return raw strings (no industry appending)

    def get_guide_overrides(self, audience_id: str) -> Dict[str, Optional[str]]:
        # Parse "## Guide Overrides" section (used in Phase 2A)
        # Returns {"original.md": "replacement.md"} or {"original.md": None} for exclude-only
        # Returns empty dict if section doesn't exist

# Module-level singleton
_loader_instance = None
def get_audience_loader() -> AudienceLoader:
    ...
```

### Step 2: Add `audience` field to `CompanyInput`

**File:** `strategy_factory/models.py` — after `logo_path` (line 70)

```python
audience: Optional[str] = Field(default=None, description="Audience ID for tailored output")
```

### Step 3: Wire audience into `ContextBuilder`

**File:** `strategy_factory/synthesis/context_builder.py`

**3a.** In `_load_tldr_knowledge()` (line 236), add `audience_id: Optional[str] = None` parameter. Don't use it yet — Phase 2A will add the override logic here.

```python
def _load_tldr_knowledge(self, deliverable_id: str, audience_id: Optional[str] = None) -> str:
```

**3b.** In `build_context()` (line 82), pass through:

```python
"tldr_knowledge": self._load_tldr_knowledge(deliverable_id, audience_id=company_input.audience),
```

**3c.** In `build_full_prompt()` (line 308), after TLDR knowledge block (after line 348), inject audience context directly:

```python
# Audience context injection
# NOTE: The full audience file (including Tone Guidance) is injected here in the user prompt.
# Tone guidance is ALSO injected separately into the system instruction (Step 4) for stronger
# influence on Gemini's writing style. This double-injection is intentional.
if company_input.audience:
    from ..audience_loader import get_audience_loader
    loader = get_audience_loader()
    audience_content = loader.load_audience(company_input.audience)
    if audience_content:
        prompt_parts.append(
            f"\n## Audience Context\n\n"
            f"The strategy should be tailored for the following audience:\n\n"
            f"{audience_content}"
        )
```

### Step 4: Add audience tone override to system instructions

**File:** `strategy_factory/synthesis/orchestrator.py`

**4a.** Change `_get_system_instruction` signature (line 224):
```python
def _get_system_instruction(self, deliverable_id: str, audience_id: Optional[str] = None) -> str:
```

**4b.** After `base_instruction` string, before return (line 238):
```python
if audience_id:
    from ..audience_loader import get_audience_loader
    tone = get_audience_loader().get_tone_guidance(audience_id)
    if tone:
        base_instruction += f"\n\n## Audience-Specific Tone Guidance\n\n{tone}"
return base_instruction
```

**4c.** In `_generate_deliverable` (line 202-204), pass audience:
```python
system_instruction=self._get_system_instruction(deliverable_id, audience_id=company_input.audience),
```

### Step 5: Add audience supplemental research queries

**File:** `strategy_factory/research/orchestrator.py`

**5a.** After Phase 6 (line 160), before "Build final output" (line 162):
```python
# Phase 7: Audience-specific supplemental queries
if company_input.audience:
    self._report_progress("audience_supplemental", 0.88)
    self._execute_audience_queries(company_input.audience, industry)
```

**5b.** New method:
```python
def _execute_audience_queries(self, audience_id: str, industry: str) -> None:
    from ..audience_loader import get_audience_loader
    loader = get_audience_loader()
    queries = loader.get_research_queries(audience_id)

    for i, query in enumerate(queries):
        # Support {industry} as optional template variable
        full_query = query.replace("{industry}", industry) if "{industry}" in query else query

        result = self.client.search(
            query=full_query,
            max_results=5,
            search_recency_filter="month",
            model="sonar",
        )
        self.results[f"audience_{audience_id}_{i}"] = result
        self._report_progress(f"audience_supplemental: query {i+1}/{len(queries)}", None)
```

### Step 6: Add `--audience` flag to CLI

**File:** `strategy_factory/main.py`

**6a.** Add argument after `--verbose` (line 140):
```python
run_parser.add_argument("--audience", "-a", type=str, default=None,
    help="Audience ID for tailored output (e.g., 'mountain_bizworks_scaleup')")
```

**6b.** Add to CompanyInput creation (line 239-244):
```python
audience=args.audience or None,
```

**6c.** Display in header (after line 227):
```python
if args.audience:
    print(f"Audience: {args.audience}")
```

### Step 7: Add audience dropdown to web app

**File:** `strategy_factory/webapp.py`

**7a.** Add dropdown HTML after Research Mode div (~line 788), before submit button:
```html
<div class="form-group">
    <label for="audience">Audience (optional)</label>
    <select id="audience" name="audience" style="...">
        <option value="">General (no audience tailoring)</option>
        {% for aud in audiences %}
        <option value="{{ aud.id }}">{{ aud.name }}</option>
        {% endfor %}
    </select>
    <small>Select an audience to tailor deliverables for a specific program or cohort</small>
</div>
```

**7b.** In home route (~line 1060), pass audiences to template:
```python
from strategy_factory.audience_loader import get_audience_loader
audiences = get_audience_loader().available_audiences
# Add audiences=audiences to Template().render(...)
```

**7c.** In `start_analysis()` (line 1071), extract audience:
```python
audience = request.form.get('audience', '').strip() or None
```

**7d.** Add to `active_jobs[job_id]` dict, thread args, and `run_pipeline` signature/CompanyInput creation — same as original plan.

### Phase 1 File Summary

| File | Action | ~Lines |
|------|--------|--------|
| `strategy_factory/audience_loader.py` | NEW | ~100 |
| `strategy_factory/models.py` | ADD 1 line | 1 |
| `strategy_factory/synthesis/context_builder.py` | ADD ~15 lines | 15 |
| `strategy_factory/synthesis/orchestrator.py` | ADD ~10 lines | 10 |
| `strategy_factory/research/orchestrator.py` | ADD ~20 lines | 20 |
| `strategy_factory/main.py` | ADD ~5 lines | 5 |
| `strategy_factory/webapp.py` | ADD ~15 lines | 15 |

**Total: ~170 lines added, 0 lines removed.**

---

## Phase 2A: Guide Overrides (revised from GUIDE-OVERRIDES.md)

### Changes from original plan

1. **Simplified override model.** No separate Exclude and Replace sections. Single `## Guide Overrides` section with replacement mappings. If the replacement file doesn't exist on disk, the original is simply excluded. If it exists, it's swapped in. One mechanism, no contradictions.
2. **Works immediately without replacement files.** The three enterprise guides get excluded even before any SMB replacement guides are created. When replacement guides are eventually added, they automatically activate.
3. **Audience creation tool deferred to Phase 2B** (separate plan, not in this document).

### Step 1: Add Guide Overrides section to audience file

**File:** `knowledge_base/audience/mountain_bizworks_scaleup.md` — append at end

```markdown
## Guide Overrides

Replace enterprise-focused consulting guides with small-business alternatives.
If a replacement file does not yet exist, the original guide is simply excluded.

- the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era_TLDR.md -> SMB_AI_team_structure_guide.md
- seizing-the-agentic-ai-advantage_TLDR.md -> SMB_quick_implementation_playbook.md
- kpmg-agentic-ai-advantage_TLDR.md -> SMB_agentic_tools_for_small_teams.md
```

### Step 2: Implement `get_guide_overrides()` in AudienceLoader

**File:** `strategy_factory/audience_loader.py` (already created in Phase 1)

```python
def get_guide_overrides(self, audience_id: str) -> Dict[str, Optional[str]]:
    """Parse '## Guide Overrides' section.

    Returns dict mapping original guide filename to replacement filename.
    If replacement file doesn't exist on disk, value is None (exclude-only).
    """
    section = self.get_section(audience_id, "Guide Overrides")
    if not section:
        return {}

    overrides = {}
    for line in section.strip().splitlines():
        line = line.strip()
        if line.startswith("- ") and " -> " in line:
            parts = line[2:].split(" -> ", 1)
            original = parts[0].strip()
            replacement = parts[1].strip()
            # Check if replacement file actually exists
            replacement_path = TLDR_GUIDES_DIR / replacement
            overrides[original] = replacement if replacement_path.exists() else None
    return overrides
```

### Step 3: Apply overrides in `_load_tldr_knowledge()`

**File:** `strategy_factory/synthesis/context_builder.py`

The `audience_id` parameter was already added in Phase 1 Step 3a. Now add the override logic:

```python
def _load_tldr_knowledge(self, deliverable_id: str, audience_id: Optional[str] = None) -> str:
    deliverable_config = DELIVERABLES.get(deliverable_id, {})
    tldr_guides = deliverable_config.get("tldr_guides", [])

    if not tldr_guides:
        return ""

    # Apply audience guide overrides
    if audience_id:
        from ..audience_loader import get_audience_loader
        overrides = get_audience_loader().get_guide_overrides(audience_id)
        if overrides:
            resolved = []
            for guide in tldr_guides:
                if guide in overrides:
                    replacement = overrides[guide]
                    if replacement:  # Replacement file exists on disk
                        resolved.append(replacement)
                    # else: exclude (don't append anything)
                else:
                    resolved.append(guide)
            tldr_guides = resolved

    # ... rest of existing loading logic unchanged ...
```

### Phase 2A File Summary

| File | Action | ~Lines |
|------|--------|--------|
| `knowledge_base/audience/mountain_bizworks_scaleup.md` | APPEND | ~8 |
| `strategy_factory/audience_loader.py` | ADD method | ~20 |
| `strategy_factory/synthesis/context_builder.py` | ADD override logic | ~15 |

**Total: ~43 lines added.**

---

## Phase 2B: Audience Creation Tool (DEFERRED)

Not in scope for this plan. Needs its own design document covering:
- Gemini prompts for audience file generation
- Criteria for identifying which guides "don't fit" an audience
- Research strategy for replacement guide topics
- Web UI (3 routes, progress polling, file preview)
- Estimated ~330+ lines of new code

---

## Verification

### Phase 1

1. **Backward compat:** `python -m strategy_factory.main run "Test Co" --dry-run` — no errors, no audience output
2. **With audience:** `python -m strategy_factory.main run "Spice Witch" --audience mountain_bizworks_scaleup --context "Specialty condiments, Asheville NC" --mode quick` — supplemental queries execute, output is tailored
3. **Web app:** `python -m strategy_factory.webapp` — dropdown shows "Mountain BizWorks ScaleUp WNC", selection persists through pipeline
4. **Resume:** Verify `state.json` preserves audience field

### Phase 2A

5. **Guide exclusion:** Run audit with `mountain_bizworks_scaleup` audience — verify the 3 enterprise guides are NOT loaded for deliverables `05_roadmap`, `14_use_case_library`, `15_change_management`, `10_ai_policy`
6. **No audience = no change:** Run without audience — all original guides load normally
7. **Future replacement activation:** Drop a test file named `SMB_AI_team_structure_guide.md` into `Consulting Guides TLDR/` — verify it gets loaded instead of the excluded guide

---

## Key Design Decisions

1. **Single Replace model** — no Exclude/Replace split. Missing replacement file = exclusion. Present replacement file = swap. One mechanism.
2. **`{industry}` as opt-in template variable** — queries control whether they want industry context, not the system.
3. **Pre-threaded `audience_id` in `_load_tldr_knowledge`** — Phase 1 adds the parameter, Phase 2A uses it. No second refactor needed.
4. **Deliberate double tone injection** — system instruction (strong influence) + user prompt (full context). Documented in code comments.
5. **All audience data in markdown** — new audiences = new .md file in a folder. No code changes.
