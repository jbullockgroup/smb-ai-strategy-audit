# WAVE 6: Final Cleanup

**Status**: Ready after Waves 1-4 land
**Depends on**: Wave 1-3 (config), Wave 4 (generation)
**Does NOT depend on**: Wave 5 (audience builder is independent)
**Source**: Extracted from REFACTOR-PLAN.md

---

## What This Wave Does

Cleans up the remaining references to old enterprise features: TLDR_TOPIC_MAPPING in config/knowledge_loader, CompanySize in models, SOW in CLI, SOW in the results page, and simplifies the existing audience file.

---

## Step 1: Remove `TLDR_TOPIC_MAPPING` — `strategy_factory/config.py` + `strategy_factory/knowledge_loader.py`

This is the last dead config constant from the original DELIVERABLES. Remove it from config and fix the only consumer:

**In `config.py`**:
- Remove `TLDR_TOPIC_MAPPING` dict

**In `knowledge_loader.py`**:
- Remove `TLDR_TOPIC_MAPPING` from the import line (keep `TLDR_GUIDES_DIR` and `DELIVERABLES`)
- Remove `load_by_topic()` method (no callers — topic-based loading is replaced by per-deliverable `tldr_guides` field)
- Remove `TLDR_TOPIC_MAPPING` references in `get_available_topics()` / any other methods that use it

---

## Step 2: Update `strategy_factory/models.py`

- Remove `CompanySize` enum class
- Remove `company_size` field default/reference on any models that use it
- Keep `audience` field on `CompanyInput` (still used for cohort context)
- Remove references to deleted deliverable IDs (anything referencing the old 15-deliverable set)

---

## Step 3: Update `strategy_factory/main.py`

- Remove SOW references from CLI output and help text
- Update dry-run output to reflect 6 deliverables (not 15)
- Keep `--audience` flag (now serves as cohort context)

---

## Step 4: Update `strategy_factory/webapp.py` — Results Page

- Remove SOW download section from results page template
- Show: Markdown files, PPTX presentation, DOCX strategy report, PDF strategy report
- Update statistics to reflect 6 deliverables (not 15)

---

## Step 5: Simplify Audience File

Update `knowledge_base/audience/mountain_bizworks_scaleup.md`:
- Remove the `## Guide Overrides` section
- Keep: Overview, Tone Guidance, Research Queries sections
- This becomes the template for audience files created via the Audience Builder (Wave 5)

---

## Step 6: Verify `strategy_factory/progress_tracker.py`

- Should need NO code changes — it reads from `DELIVERABLES` config dynamically
- Verify it handles 6 deliverables correctly (run a dry-run to confirm)

---

## Step 7: Enterprise Consulting Guides — Leave As-Is

The 10 enterprise guides in `Consulting Guides TLDR/` (BCG, KPMG, Google Cloud, etc.) stay on disk. They're simply never referenced. No files deleted.

The 3 SMB guides used are:
- `smb-ai-playbook.md`
- `smb-ai-value-playbook.md`
- `ai-implementation-steps-smb.md`

---

## Files Changed in This Wave

| File | Action |
|------|--------|
| `strategy_factory/config.py` | Remove `TLDR_TOPIC_MAPPING` |
| `strategy_factory/knowledge_loader.py` | Remove `TLDR_TOPIC_MAPPING` import and topic-based methods |
| `strategy_factory/models.py` | Remove `CompanySize` enum, old deliverable ID refs |
| `strategy_factory/main.py` | Remove SOW refs, update help text |
| `strategy_factory/webapp.py` | Results page: remove SOW section |
| `knowledge_base/audience/mountain_bizworks_scaleup.md` | Simplify, remove Guide Overrides |

## Verification

```bash
# Full pipeline dry run — should show clean 6-deliverable plan
python -m strategy_factory.main run "Test Company" --dry-run

# End-to-end quick mode
python -m strategy_factory.main run "Burris Chalmers Communications" --mode quick

# Verify output:
# - Markdown directory has exactly 6 .md files
# - Documents directory has 1 .docx and 1 .pdf
# - Presentations directory has 1 .pptx
# - No SOW generated
# - Report is ~15-20 pages
# - 1-2 page executive summary at front
# - NO: ADKAR, BCG, maturity curves, governance, stakeholder matrices
# - YES: specific tool names, prices, concrete actions

# Audience test
python -m strategy_factory.main run "Test Company" --audience mountain_bizworks_scaleup
# - Cohort context should appear in output
# - WNC/regional references should be present

# Webapp results page
python -m strategy_factory.webapp
# - Results page shows: markdown, pptx, docx, pdf downloads
# - No SOW sections
# - Statistics reflect 6 deliverables
```
