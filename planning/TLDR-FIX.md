# TLDR-FIX.md — Fix knowledge_loader.py

**Purpose**: Self-contained handoff document for a new agent session. Contains everything needed to fix the broken knowledge loader.

## Execution Order: Step 1 of 5

Standalone — no prerequisites, no downstream dependencies. Can run anytime before or in parallel with steps 2-5.

## Why This Change

The repo was reoriented from enterprise to SMB. The TLDR guide files were replaced (old: `bcg-wheres-the-value-in-ai_TLDR.md`, new: `smb-ai-playbook.md`), but `knowledge_loader.py` was never updated.

**What's broken:**
- The glob pattern `*_TLDR.md` on line 50 matches zero files — the current SMB guide files don't use that naming convention
- `get_key_frameworks()` (line 266) references deleted enterprise files like `bcg-wheres-the-value-in-ai_TLDR.md`
- `extract_framework()` (line 237) and `get_key_frameworks()` are never called anywhere in the codebase — they're dead code

**What still works (don't break it):**
- `load_guide()` loads by direct filename — this path works fine
- `load_for_deliverable()` calls `load_guide()` with filenames from config.py — also works
- `config.py` references `smb-ai-playbook.md`, `smb-ai-value-playbook.md`, `ai-implementation-steps-smb.md` — these files all exist in `Consulting Guides TLDR/`

---

## File to Edit: `strategy_factory/knowledge_loader.py`

### Change 1: Fix the glob pattern (line 50)

**Current:**
```python
self._available_guides = [
    f.name for f in self.guides_dir.glob("*_TLDR.md")
]
```

**New:**
```python
self._available_guides = [
    f.name for f in self.guides_dir.glob("*.md")
]
```

This correctly discovers `smb-ai-playbook.md`, `ai-implementation-steps-smb.md`, `smb-ai-value-playbook.md`, and all other SMB guide files. Non-`.md` files and subdirectories (`OLD PROMPTS`, `ORIGINAL SOURCES`) are excluded automatically.

### Change 2: Delete dead code (lines 236-314)

Delete both functions at the bottom of the file:
- `extract_framework()` (starts line 237)
- `get_key_frameworks()` (starts line 266)
- The module-level comment `# Framework extraction helpers` (line 236)

Neither is called anywhere in the codebase. They reference enterprise files that no longer exist and serve no purpose.

### Change 3: Update docstring example (line 31)

**Current:**
```python
content = loader.load_guides(["bcg-wheres-the-value-in-ai_TLDR.md"])
```

**New:**
```python
content = loader.load_guides(["smb-ai-playbook.md"])
```

---

## Verification

Run this after implementation:

```bash
cd /Users/jeff/ai-strategy-factory
source venv/bin/activate
python -c "
from strategy_factory.knowledge_loader import KnowledgeLoader
loader = KnowledgeLoader()
print('Available guides:', len(loader.available_guides))
for g in loader.available_guides:
    print(' -', g)
content = loader.load_for_deliverable('01_tools_audit')
print('Loaded for 01_tools_audit:', len(content), 'chars')
content2 = loader.load_for_deliverable('02_daily_pain_points')
print('Loaded for 02_daily_pain_points:', len(content2), 'chars')
"
```

**Expected results:**
- `Available guides:` should show ~16 files (all the `.md` files in `Consulting Guides TLDR/`)
- Each `load_for_deliverable()` call should return non-empty content
- No errors or warnings

**Confirm these functions no longer exist:**
```bash
grep -n "extract_framework\|get_key_frameworks" strategy_factory/knowledge_loader.py
```
Should return no matches.
