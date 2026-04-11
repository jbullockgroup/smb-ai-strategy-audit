# AUDIENCE-REDUX: Lightweight Audience System with AI-Enriched Builder

## Why This Change

The audience system was originally built to steer prompts toward specific cohorts via interview-style audience files. Since then, the entire pipeline has been re-engineered for SMB — the system instruction, all prompt templates, and the knowledge base are already SMB-specific. The current audience file (`mountain_bizworks_scaleup.md`, 218 lines) injects noise into every prompt.

This plan does three things:
1. **Simplifies the audience format** to a short business-context paragraph (5-10 lines)
2. **Replaces the interview-style builder** with an AI-enriched generator that researches the vertical+region intersection and produces context the user wouldn't think of themselves — with an editable textarea so the user can revise before saving
3. **Moves audience injection below additional context** in the prompt for organizational clarity

---

## Current Architecture (What Exists Now)

### Files Involved

| File | Role |
|------|------|
| `strategy_factory/audience_loader.py` | Loads `*.md` from `knowledge_base/audience/`, extracts sections (Tone Guidance, Research Queries, Guide Overrides) |
| `strategy_factory/models.py:63` | `CompanyInput.audience: Optional[str]` — the audience ID field |
| `strategy_factory/main.py` | CLI `--audience` / `-a` argument |
| `strategy_factory/webapp.py` | Dropdown in start form, audience builder page (`/audience-builder`), chat endpoint (`/audience-builder/chat`), save endpoint (`/audience-builder/save`) |
| `strategy_factory/research/orchestrator.py` | Fires supplemental Perplexity queries from audience `## Research Queries` section (lines 128-131, 207-223) |
| `strategy_factory/synthesis/context_builder.py` | Injects ENTIRE audience `.md` file into every prompt (lines 287-297) |
| `strategy_factory/synthesis/orchestrator.py` | `_get_system_instruction()` accepts `audience_id` but ignores it — hardcoded SMB instruction (lines 197, 217-233) |
| `knowledge_base/audience/mountain_bizworks_scaleup.md` | The one existing audience file: 218 lines, 13 business profiles, cohort analysis, tone guidance, research queries |

### Current Prompt Injection Order (in `context_builder.py:build_full_prompt()`)

1. Temporal context (date)
2. Company name
3. Company profile (from research)
4. Industry context (from research)
5. Tech landscape (from research)
6. TLDR knowledge guides
7. **Audience context** (entire file, line 287)
8. Dependencies (previous deliverables)
9. **Additional context from client** (user input, line 306)
10. The actual prompt template

### Current Audience Builder Flow

The builder is an interview: user types something, AI asks 2-3 clarifying questions, then suggests a name. The AI only reformats what the user tells it — it doesn't research or enrich. Located in `webapp.py`:
- Chat endpoint: lines 1649-1705
- Save endpoint: lines 1708-1778
- HTML (`AUDIENCE_BUILDER_CONTENT`): lines 1455-1496
- JavaScript (`AUDIENCE_BUILDER_SCRIPTS`): lines 1498-1596

---

## Implementation Steps

### Step 1: Rewrite the audience file

**File**: `knowledge_base/audience/mountain_bizworks_scaleup.md`

Replace entire 218-line contents with:

```markdown
# Mountain BizWorks ScaleUp WNC

## Business Context

WNC tourism-driven economy with strong seasonal fluctuations and a celebrated craft/maker heritage.
Revenue range $150K-$2.5M; most are owner-only or 1-3 FTE. Community-oriented values dominate:
personal relationships, handmade quality, local sourcing, inclusivity. Common growth vectors are
product-to-channel expansion (e.g., farmers market to wholesale), local-to-regional scaling via
e-commerce, and maker/artisan scaling without losing craft quality. Post-Helene recovery context
makes resilience messaging relevant. Women-owned and underrepresented founders are prominent.
```

Format rules: H1 title, single `## Business Context` section, 5-10 lines, no other sections.

---

### Step 2: Simplify `audience_loader.py`

**File**: `strategy_factory/audience_loader.py`

**Current code** (142 lines): Has `get_section()`, `get_tone_guidance()`, `get_research_queries()`, `get_guide_overrides()` methods, imports `datetime` and `TLDR_GUIDES_DIR`.

**Remove** these methods:

| Method | Lines | Why remove |
|--------|-------|-----------|
| `get_section()` | 75-83 | Only one section now; replace with targeted method |
| `get_tone_guidance()` | 85-87 | Redundant with system instruction |
| `get_research_queries()` | 89-107 | Research orchestrator handles queries |
| `get_guide_overrides()` | 109-129 | Never called from production code |

Also remove:
- `from datetime import datetime` (only used by `get_research_queries`)
- `from .config import TLDR_GUIDES_DIR` (only used by `get_guide_overrides`)

Update the docstring to remove references to tone guidance, research queries, and guide overrides.

**Add**:

```python
def get_business_context(self, audience_id: str) -> str:
    """Extract the ## Business Context paragraph from an audience file."""
    content = self.load_audience(audience_id)
    if not content:
        return ""
    pattern = r"^##\s+Business Context\s*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""
```

**Keep unchanged**: `AUDIENCE_DIR` constant, `available_audiences` property, `load_audience()` method, `_cache` dict, `get_audience_loader()` singleton factory.

---

### Step 3: Update `context_builder.py` — reorder injection

**File**: `strategy_factory/synthesis/context_builder.py`

**Current code** at lines 287-309 in `build_full_prompt()`:

```python
# Audience context — cohort context for tailoring (e.g., "plumbers in NC")
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

# Add dependencies
if context["dependencies"]:
    prompt_parts.append(
        f"\n{self.format_dependencies_for_prompt(context['dependencies'])}"
    )
    
# Add user context if provided
if context["company_context"]:
    prompt_parts.append(
        f"\n## Additional Context from Client\n{context['company_context']}"
    )
```

**Replace with** (reorders so additional context comes before audience, and uses the new `get_business_context()` instead of full file injection):

```python
# Add user context if provided
if context["company_context"]:
    prompt_parts.append(
        f"\n## Additional Context from Client\n{context['company_context']}"
    )

# Business context — regional/cultural context research can't surface
if company_input.audience:
    from ..audience_loader import get_audience_loader
    loader = get_audience_loader()
    business_context = loader.get_business_context(company_input.audience)
    if business_context:
        prompt_parts.append(f"\n## Business Context\n{business_context}")

# Add dependencies
if context["dependencies"]:
    prompt_parts.append(
        f"\n{self.format_dependencies_for_prompt(context['dependencies'])}"
    )
```

**New prompt injection order**:
1-6. (unchanged)
7. **Additional context from client** (moved up)
8. **Business context** (audience, moved down)
9. Dependencies
10. The actual prompt template

---

### Step 4: Remove audience research queries

**File**: `strategy_factory/research/orchestrator.py`

**Remove** lines 128-131:
```python
# Audience-specific supplemental queries
if company_input.audience:
    self._report_progress("audience_supplemental", 0.85)
    self._execute_audience_queries(company_input.audience, industry)
```

**Remove** the entire `_execute_audience_queries()` method (lines 207-223):
```python
def _execute_audience_queries(self, audience_id: str, industry: str) -> None:
    """Execute audience-specific supplemental research queries."""
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
        )
        self.results[f"audience_{audience_id}_{i}"] = result
        self._report_progress(f"audience_supplemental: query {i+1}/{len(queries)}", None)
```

---

### Step 5: Clean up `synthesis/orchestrator.py`

**File**: `strategy_factory/synthesis/orchestrator.py`

**Change** `_get_system_instruction()` signature at line 217:
- Remove `audience_id: Optional[str] = None` parameter (was accepted but never used)
- Method body stays the same

Current:
```python
def _get_system_instruction(self, deliverable_id: str, audience_id: Optional[str] = None) -> str:
```

New:
```python
def _get_system_instruction(self, deliverable_id: str) -> str:
```

**Update** the call site at line 197:
```python
# Before:
system_instruction=self._get_system_instruction(deliverable_id, audience_id=company_input.audience),
# After:
system_instruction=self._get_system_instruction(deliverable_id),
```

---

### Step 6: Replace audience builder with AI-enriched generator + editable draft

**File**: `strategy_factory/webapp.py`

This is the major change. The builder goes from an interview to a one-shot research+generate flow with an editable textarea.

#### 6a. Replace `/audience-builder/chat` endpoint (line 1649)

**New flow**:
1. User types a short description (e.g., "plumbers in Western North Carolina")
2. On the first message only, system fires 2-3 Perplexity searches targeting the vertical+region intersection
3. Gemini synthesizes research into a draft business context paragraph
4. Draft appears both as a chat message AND in an editable textarea below the chat
5. User can refine via follow-up chat messages OR directly edit the textarea
6. The textarea content is what gets saved

**New system instruction**:
```python
system_instruction = (
    "You are generating a business context profile for an AI strategy tool used by small business consultants. "
    "You will receive a short description of a business vertical and region (e.g., 'plumbers in Western North Carolina' "
    "or 'lawyers in St. Louis'). Your job is to enrich it with specific, actionable regional and vertical context "
    "that web research cannot easily surface for individual companies. Cover: regional economy drivers, typical "
    "business structure (owner-only vs staff, revenue range), local regulatory or licensing specifics, cultural "
    "or community factors, industry-specific challenges in that geography, and growth patterns common to that "
    "vertical in that region. Be specific — name real conditions, not generic advice. Write in a single flowing "
    "paragraph, 5-10 lines. If the user sends a follow-up message, revise the paragraph to incorporate their feedback. "
    "On the first response, also suggest a short profile name (5 words or less) on its own line prefixed with "
    "'Suggested name: '. Keep the paragraph itself separate from the name suggestion."
)
```

**Add Perplexity research before Gemini generation** (first user turn only):
```python
# Count user turns
user_turns = sum(1 for h in history if h['role'] == 'user')

# On first user message, enrich with Perplexity research
if user_turns == 1:
    from strategy_factory.research.perplexity_client import PerplexityClient
    from strategy_factory.config import PerplexityModel
    pplx = PerplexityClient()
    user_desc = history[-1]['content']

    research_queries = [
        f"{user_desc} typical business structure revenue range challenges",
        f"{user_desc} regional market conditions regulatory requirements",
        f"AI adoption trends {user_desc} small business",
    ]

    research_context = ""
    for q in research_queries:
        try:
            result = pplx.search(query=q, max_results=5, model=PerplexityModel.SONAR)
            snippets = "; ".join(r.snippet for r in result.results[:3] if r.snippet)
            research_context += f"- {q}: {snippets}\n"
        except Exception:
            pass  # Graceful degradation — generate without research if Perplexity fails

    # Prepend research to the conversation for Gemini
    conversation = f"Research findings about '{user_desc}':\n{research_context}\n\n{conversation}"
```

**Adjust readiness**: Set `ready_to_save = True` after first turn (since the draft is generated immediately).

**Extract draft text for the editor**: Parse the business context paragraph out of the reply so it can populate the editable textarea. The reply contains the paragraph plus a suggested name line — strip the name line and return just the paragraph as `draft_text`:
```python
# Extract paragraph (everything before "Suggested name:" line, stripped)
draft_text = reply
name_match = _re.search(r'\n[Ss]uggested name:.*', draft_text)
if name_match:
    draft_text = draft_text[:name_match.start()].strip()

return jsonify({
    "reply": reply,
    "draft_text": draft_text,
    "turn_count": user_turns,
    "ready_to_save": ready_to_save,
    "suggested_name": suggested_name,
})
```

#### 6b. Replace `/audience-builder/save` endpoint (line 1708)

**New behavior**: Accept `draft_text` directly from the request. If provided, use it as-is (the user already edited it in the textarea). Fall back to generating from chat history if `draft_text` is absent (backward compatible).

```python
@app.route('/audience-builder/save', methods=['POST'])
def audience_builder_save():
    """Generate and save the audience file from chat history or edited draft."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "Audience name is required"}), 400

    try:
        from strategy_factory.progress_tracker import slugify
        from strategy_factory.audience_loader import AUDIENCE_DIR
        import strategy_factory.audience_loader as _al_module

        draft_text = data.get('draft_text', '').strip()

        if draft_text:
            # User edited the draft in textarea — use it directly
            file_content = f"# {name}\n\n## Business Context\n\n{draft_text}\n"
        else:
            # Fallback: generate from chat history
            history = data.get('history', [])
            conversation = "\n".join(
                f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
                for h in history
            )

            from strategy_factory.synthesis.gemini_client import GeminiClient
            client = GeminiClient()

            prompt = f"""Based on this conversation and research, generate a concise business context profile.

Conversation:
{conversation}

Profile name: {name}

Generate the file in exactly this Markdown format (output only the file content, nothing else):

# {name}

## Business Context
[5-10 lines covering: regional economy context, revenue range if known, team structure
(owner-only vs staff), values/culture notes, and industry-specific context that web
research cannot easily surface. Write as a single flowing paragraph. Be specific, not generic.]
"""
            result = client.generate(
                prompt=prompt,
                temperature=0.7,
                max_output_tokens=1024,
            )
            if result.error:
                return jsonify({"error": result.error}), 500
            file_content = result.content.strip()

        # Save to file
        slug = slugify(name)
        AUDIENCE_DIR.mkdir(parents=True, exist_ok=True)
        save_path = AUDIENCE_DIR / f"{slug}.md"
        save_path.write_text(file_content, encoding="utf-8")

        # Invalidate singleton cache so new audience appears in dropdown
        _al_module._loader_instance = None

        return jsonify({"slug": slug, "name": name})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

#### 6c. Add editable draft textarea to builder page

**HTML changes** — in `AUDIENCE_BUILDER_CONTENT` (starts line 1455), add a new section between the chat container `</div>` and the save section `<div id="save-section">`:

```html
<div id="draft-section" style="display: none; margin-top: 1rem;">
    <div class="form-group">
        <label for="draft-editor">Generated Business Context <small>(edit before saving)</small></label>
        <textarea id="draft-editor" rows="8" style="width: 100%; font-family: monospace; font-size: 0.9rem; padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; resize: vertical;"></textarea>
    </div>
</div>
```

**JavaScript changes** — in `AUDIENCE_BUILDER_SCRIPTS` (starts line 1498):

In `sendMessage()`, after `appendMessage('assistant', data.reply)` and the chatHistory push, add:
```javascript
if (data.draft_text) {
    document.getElementById('draft-section').style.display = 'block';
    document.getElementById('draft-editor').value = data.draft_text;
}
```

In `saveAudience()`, replace the logic to send the textarea content:
```javascript
async function saveAudience() {
    const name = document.getElementById('audience-name').value.trim();
    if (!name) {
        alert('Please enter a profile name.');
        return;
    }

    const draftText = document.getElementById('draft-editor').value.trim();
    if (!draftText) {
        alert('No draft to save. Generate one first.');
        return;
    }

    const saveBtn = document.getElementById('save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    try {
        const resp = await fetch('/audience-builder/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: name, draft_text: draftText, history: chatHistory})
        });
        const data = await resp.json();

        if (data.error) {
            document.getElementById('save-error').style.display = 'block';
            document.getElementById('error-text').textContent = data.error;
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Profile';
        } else {
            document.getElementById('save-section').style.display = 'none';
            document.getElementById('draft-section').style.display = 'none';
            document.getElementById('save-success').style.display = 'block';
            document.getElementById('save-message').textContent = 'Profile "' + data.name + '" saved successfully.';
        }
    } catch(e) {
        document.getElementById('save-error').style.display = 'block';
        document.getElementById('error-text').textContent = 'Network error: ' + e.message;
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Profile';
    }
}
```

#### 6d. Update builder page labels

In `AUDIENCE_BUILDER_CONTENT`:
- `<h2>Audience Builder</h2>` → `<h2>Business Context Profile Builder</h2>`
- Helper text: `"Describe a business cohort and chat with AI to refine it into a saved audience file. Audience files tailor deliverable language for specific programs or customer segments."` → `"Describe a business vertical and region. AI will research and generate a context profile you can edit before saving."`
- Chat input placeholder: `"e.g. Plumbers in western North Carolina, 2-5 employees"` → `"e.g., plumbers in Western North Carolina"`
- Save button text: `Save Audience` → `Save Profile`

In the `/audience-builder` route handler (line ~1638-1646), update the page title if one is set.

---

### Step 7: Update labels in `main.py` and `models.py`

**File**: `strategy_factory/main.py` (line ~145):
```python
help="Business context profile ID for regional/cultural tailoring (e.g., 'mountain_bizworks_scaleup')",
```

**File**: `strategy_factory/models.py` (line 63):
```python
audience: Optional[str] = Field(default=None, description="Business context profile ID for regional/cultural tailoring")
```

Field name stays `audience` for backward compatibility.

---

### Step 8: Update webapp start form dropdown label

**File**: `strategy_factory/webapp.py`

In the main page start form (where the audience dropdown appears), update:
- Label: "Audience" → "Business Context"
- Default option: "General (no audience tailoring)" → "General (no regional context)"
- "Create New Audience" link → "Create New Profile"
- Helper text: update to match new terminology

---

## What Gets Removed vs. Kept

| What | Where | Action |
|------|-------|--------|
| 218-line audience file | `mountain_bizworks_scaleup.md` | **Replace** with 6-line paragraph |
| `get_section()` | `audience_loader.py` | **Remove** |
| `get_tone_guidance()` | `audience_loader.py` | **Remove** |
| `get_research_queries()` | `audience_loader.py` | **Remove** |
| `get_guide_overrides()` | `audience_loader.py` | **Remove** |
| `_execute_audience_queries()` | `research/orchestrator.py` | **Remove** |
| Audience query execution block | `research/orchestrator.py:128-131` | **Remove** |
| `audience_id` param | `synthesis/orchestrator.py` | **Remove** |
| Full file injection | `context_builder.py:287-309` | **Replace** with paragraph injection, reorder |
| Interview-style builder system instruction | `webapp.py` chat endpoint | **Replace** with enrichment instruction |
| Interview-style save prompt | `webapp.py` save endpoint | **Replace** with draft_text passthrough + fallback |
| `available_audiences` | `audience_loader.py` | **Keep** |
| `load_audience()` | `audience_loader.py` | **Keep** |
| `get_audience_loader()` | `audience_loader.py` | **Keep** |
| Dropdown mechanism | `webapp.py` start form | **Keep** (update labels) |
| CLI `--audience` flag | `main.py` | **Keep** (update help text) |
| `CompanyInput.audience` field | `models.py` | **Keep** (update description) |

---

## Edge Cases

- **Old-format audience files**: If someone has an old `.md` file without `## Business Context`, `get_business_context()` returns `""`. The prompt simply omits audience context. No error, no crash.
- **No audience selected**: `company_input.audience` is `None` — all the `if company_input.audience:` guards skip cleanly. Same behavior as today.
- **Perplexity unavailable in builder**: Graceful degradation — Gemini generates from its own knowledge without research enrichment. The `try/except` around each Perplexity query silently skips failures.
- **User sends follow-up**: Second turn skips Perplexity (only fires on `user_turns == 1`), Gemini revises the draft based on user feedback, textarea gets updated with new draft.
- **User edits textarea then sends follow-up chat**: The chat revision updates the textarea, potentially overwriting user edits. This is acceptable — user can re-edit after revision.

---

## Verification

1. **Import check**: `python -c "from strategy_factory.audience_loader import get_audience_loader; l = get_audience_loader(); print(l.available_audiences); print(l.get_business_context('mountain_bizworks_scaleup'))"` — should list audience and print context paragraph
2. **Dry run with audience**: `python -m strategy_factory.main run "Test Company" --audience mountain_bizworks_scaleup --dry-run` — no import or attribute errors
3. **Dry run without audience**: `python -m strategy_factory.main run "Test Company" --dry-run` — works identically to before
4. **Full pipeline with audience**: Run a strategy with `--audience mountain_bizworks_scaleup`, check markdown output for WNC/regional context influence
5. **Full pipeline without audience**: Run without `--audience`, should produce identical output to pre-change behavior
6. **Webapp builder — generation**: Type "lawyers in St. Louis Missouri" in builder, verify Perplexity research fires, verify draft paragraph appears in chat AND in editable textarea
7. **Webapp builder — editing**: Edit the textarea content, verify the edited text (not the chat text) is what gets saved to the `.md` file
8. **Webapp builder — follow-up**: After draft, type a refinement in chat, verify textarea gets updated with revised draft
9. **Webapp builder — save and use**: Save the profile, return to main page, verify it appears in dropdown, run a strategy with it selected
