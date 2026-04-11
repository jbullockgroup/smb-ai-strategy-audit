# Plan: Remove All Mermaid Diagram Code

## Context

Mermaid diagram generation is dead code that lingers across the codebase. The pipeline no longer generates or uses mermaid diagrams, but remnants persist in 6 files. A prior pass already removed all PPTX-related code including `pptx_generator.py` (the heaviest consumer of mermaid). This plan cleans up what remains.

**All changes are removals only — no new code needed.**

## Scope

**6 files** (1 deleted, 5 edited).

---

## 1. DELETE: `strategy_factory/generation/mermaid_renderer.py`

This entire 451-line file is dedicated solely to mermaid diagram rendering. Delete it completely.

- It is **not** imported in `strategy_factory/generation/__init__.py` — no import cleanup needed there
- It is **not** imported anywhere else in the codebase

---

## 2. EDIT: `strategy_factory/generation/docx_generator.py`

**Lines 432–443**: The code block handler has a mermaid-specific skip branch. Replace it with a simple toggle:

```python
# CURRENT (lines 432-443):
if stripped.startswith('```'):
    # If we're starting a code block, check if it's mermaid (skip entirely)
    if not in_code_block and 'mermaid' in stripped.lower():
        # Skip the entire mermaid block
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('```'):
            i += 1
        i += 1  # Skip closing ```
        continue
    in_code_block = not in_code_block
    i += 1
    continue

# REPLACE WITH:
if stripped.startswith('```'):
    in_code_block = not in_code_block
    i += 1
    continue
```

---

## 3. EDIT: `strategy_factory/generation/pdf_generator.py`

**Lines 559–565**: The code block handler has a mermaid-specific skip branch. Remove it, keeping only the code block toggle:

```python
# CURRENT (lines 559-565):
if stripped.startswith("```"):
    if not in_code_block and "mermaid" in stripped.lower():
        i += 1
        while i < len(lines) and not lines[i].strip().startswith("```"):
            i += 1
        i += 1
        continue
    if in_code_block and code_lines:

# REPLACE WITH:
if stripped.startswith("```"):
    if in_code_block and code_lines:
```

---

## 4. EDIT: `strategy_factory/generation/markdown_generator.py`

**Lines 243–288**: Delete the entire `extract_mermaid_blocks()` method. It is never called anywhere in the codebase. The method starts at line 243 with `def extract_mermaid_blocks(self, content: str) -> List[Dict[str, str]]:` and ends at line 288 with `return blocks`.

---

## 5. EDIT: `strategy_factory/server.py`

Three sections to clean up:

### 5a. Lines 59–67 — Mermaid image collection

```python
# DELETE this entire block:
    # Check for mermaid images
    mermaid_images = []
    mermaid_dir = output_dir / "mermaid_images"
    if mermaid_dir.exists():
        for img in sorted(mermaid_dir.glob("*.png")):
            mermaid_images.append({
                "name": img.stem.replace("_", " ").title(),
                "path": f"/mermaid_images/{img.name}"
            })
```

### 5b. Lines 412–415 — Diagrams stat card in HTML template

```html
<!-- DELETE this stat card: -->
                <div class="stat">
                    <div class="stat-value">{len(mermaid_images)}</div>
                    <div>Diagrams</div>
                </div>
```

### 5c. Lines 480–488 — diagramsHtml JavaScript template and image loop

```python
# DELETE the diagramsHtml template string and the for loop entirely
# (do not leave an empty `const diagramsHtml = ''` — the variable has no
# remaining consumers once 5d/5e/5f below are applied):
    const diagramsHtml = `
        <h1>System Architecture Diagrams</h1>
        <div class="diagrams-grid">
"""

    for img in mermaid_images:
        html += f'                <div class="diagram-card"><img src="{img["path"]}" alt="{img["name"]}" loading="lazy"><h4>{img["name"]}</h4></div>\n'

    html += """            </div>
    `;
```

After deletion, the surrounding `html += """..."""` string that previously opened the `<script>` block should be merged with whatever follows so the JavaScript still parses.

### 5d. Lines 436–440 — Sidebar "Diagrams" section

```html
<!-- DELETE this entire sidebar block: -->
                <h3>Diagrams</h3>
                <ul class="nav-list">
                    <li><a href="#" id="diagrams-link">View All Diagrams</a></li>
                </ul>
```

Without this, the "View All Diagrams" link is gone and nothing in the sidebar points at removed functionality.

### 5e. Lines 469–472 — "Architecture Diagrams" quick-link card

```html
<!-- DELETE this quick-link card from the welcome grid: -->
                        <a href="#" class="quick-link" id="quick-diagrams">
                            <h4>Architecture Diagrams</h4>
                            <p>Visual system overview</p>
                        </a>
```

### 5f. Lines 511–514 and 537–551 — `showDiagrams()` function and its event listeners

```javascript
// DELETE the showDiagrams() function (lines 511-514):
        function showDiagrams() {
            document.getElementById('content').innerHTML = diagramsHtml;
            document.querySelectorAll('.nav-list a').forEach(a => a.classList.remove('active'));
        }

// DELETE both event-listener blocks (lines 537-551):
            // Diagrams links
            const diagramsLink = document.getElementById('diagrams-link');
            if (diagramsLink) {
                diagramsLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    showDiagrams();
                });
            }

            const quickDiagrams = document.getElementById('quick-diagrams');
            if (quickDiagrams) {
                quickDiagrams.addEventListener('click', function(e) {
                    e.preventDefault();
                    showDiagrams();
                });
            }
```

After 5a–5f, `server.py` has no references to `mermaid_images`, `diagramsHtml`, `showDiagrams`, `diagrams-link`, or `quick-diagrams` — no dead variables and no broken links.

---

## 6. EDIT: `strategy_factory/main.py`

**Lines 782–786**: Delete the mermaid image listing block:

```python
# DELETE:
        # List mermaid images
        mermaid_dir = output_dir / "mermaid_images"
        if mermaid_dir.exists():
            img_files = list(mermaid_dir.glob("*.png"))
            print(f"  Diagrams: {len(img_files)} images")
```

---

## Files That Do NOT Need Changes

- `strategy_factory/generation/__init__.py` — does not import `mermaid_renderer`
- `strategy_factory/generation/orchestrator.py` — mermaid references were in PPTX calls that were already removed
- `strategy_factory/generation/pptx_generator.py` — already deleted in prior PPTX removal pass

---

## Verification Steps

After all edits:

1. **Grep check**: `grep -ri mermaid strategy_factory/ --include="*.py"` should return zero results
2. **Import check**: `python -c "from strategy_factory.generation import run_generation"` should succeed
3. **Web app import**: `python -c "from strategy_factory.server import app"` should succeed
4. **Dry run**: `python -m strategy_factory.main run "Test Company" --dry-run` should complete without errors

## Notes for the Implementing Agent

- All changes are **removals only** — no new code needed
- The `mermaid_renderer.py` file is standalone with no imports elsewhere, safe to delete outright
- In `docx_generator.py` and `pdf_generator.py`, the mermaid skip branches scan the markdown source for ```` ```mermaid ```` fences — they are dead because the pipeline no longer *produces* such fences, not because of any runtime flag. Removing them simplifies the code block handling to a standard toggle; any legacy cached markdown containing a mermaid fence would now render as a plain code block, which is acceptable
- In `server.py`, removing the `mermaid_images` variable and the diagramsHtml template also removes the only place `mermaid_images` was used, so no dangling references will remain
- Line numbers are approximate — always verify the surrounding code matches before making edits
