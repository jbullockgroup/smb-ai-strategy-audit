# WAVE 5: Audience Builder (New Feature)

**Status**: Ready — fully independent, can be done in parallel with Wave 4
**Depends on**: Wave 1-3 (needs new config, does NOT depend on Wave 4)
**Source**: Extracted from REFACTOR-PLAN.md

---

## What This Wave Does

Adds a new `/audience-builder` page to the webapp where Jeff describes a cohort in plain text, Gemini refines it through a chat interaction, and saves it as an audience file. This is purely additive — no existing code paths are modified.

---

## Implementation

### New Route: `/audience-builder` in `strategy_factory/webapp.py`

**GET** — Renders the page with a chat interface:
- Text area for describing the audience/cohort
- Chat history display
- "Save Audience" button (appears after sufficient refinement)

**POST** — Handles chat interaction:
- User describes audience/cohort in plain text
- POST sends to Gemini for refinement
- Gemini asks 2-3 follow-up questions via chat
- On "Save Audience" button press, Gemini generates the final file

### Gemini Integration

- Use existing `gemini_client.py` for the chat refinement
- System instruction for Gemini: "You are helping a small business AI coach define an audience cohort. Ask 2-3 clarifying questions about their industry, size, tech comfort, and regional context. Then generate a structured audience file."
- Chat messages stored in session context (not persisted between sessions)

### Save Logic

- Saved to `knowledge_base/audience/{slug}.md`
- Slug derived from audience name (lowercase, hyphens, no special chars)
- After saving, new audience appears in main page dropdown

### File Format

```markdown
# {Audience Name}

## Overview
{Description of the cohort}

## Tone Guidance
{How to tailor output for this audience}

## Research Queries
- {query 1}
- {query 2}
- {query 3}
```

---

## Files Changed in This Wave

| File | Action |
|------|--------|
| `strategy_factory/webapp.py` | Add `/audience-builder` GET/POST routes + HTML template |

That's it. One file, purely additive.

---

## Also Update: Main Page (Minor)

While in `webapp.py`, also add to the main page:
- A "Create New Audience" button linking to `/audience-builder`

This is a one-line HTML addition to the existing main page template.

---

## Verification

```bash
# Start webapp
python -m strategy_factory.webapp

# Manual test:
# 1. Open /audience-builder
# 2. Type: "Plumbers in western North Carolina, 2-5 employees"
# 3. Chat with Gemini (should ask follow-up questions)
# 4. Click "Save Audience"
# 5. Verify file exists at knowledge_base/audience/plumbers-wnc.md
# 6. Go to main page — verify new audience appears in dropdown
```
