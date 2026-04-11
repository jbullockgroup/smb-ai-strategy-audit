# Plan: Add Delete Button to Sidebar Company Cards

## Context

The AI Strategy Factory webapp (`strategy_factory/webapp.py`) shows previous analyses as clickable cards in a left sidebar. Users have no way to remove old or incorrect analyses. The goal is to add a red X button that appears on hover (right side of each card) to delete that analysis.

All changes are in a single file: **`strategy_factory/webapp.py`** — the entire UI is inline HTML/CSS/JS in Python string constants, with no separate template files.

---

## How the Sidebar Currently Works

### Card HTML (Jinja2 template at ~line 848)
```html
{% for company in companies %}
<a href="/results/{{ company.slug }}" class="sidebar-company-card" data-name="{{ company.name|lower }}">
    <div class="sidebar-company-name">{{ company.name }}</div>
    <div class="sidebar-company-meta">
        <span class="sidebar-phase">{{ company.phase }}</span>
        <span class="sidebar-progress">{{ "%.0f"|format(company.progress) }}%</span>
    </div>
</a>
{% endfor %}
```

### Card CSS (~line 738)
```css
.sidebar-company-card {
    display: block;
    padding: 0.75rem;
    border-radius: 6px;
    text-decoration: none;
    color: var(--text);
    transition: background 0.15s;
    border-bottom: 1px solid var(--border);
}
.sidebar-company-card:hover {
    background: var(--bg);
}
```

### Card click behavior (JS in `HOME_SCRIPTS` ~line 949)
The cards are plain `<a>` tags — clicking navigates to `/results/<slug>`. The search filter uses `data-name` attribute and `sidebarList.querySelectorAll('.sidebar-company-card')`.

### Data source
The home route (`/` at ~line 1181) iterates `OUTPUT_DIR` directories, loads each `state.json` via `ProgressTracker`, and builds a list of company dicts with `name`, `slug`, `phase`, `progress`, `cost`.

---

## Implementation Plan (4 changes in webapp.py)

### Change 1: Add CSS (~line 745, after existing card styles)

Add these rules alongside the existing `.sidebar-company-card` styles:

```css
.sidebar-company-card {
    position: relative;  /* ADD THIS to existing rule */
}

.delete-btn {
    position: absolute;
    top: 50%;
    right: 0.5rem;
    transform: translateY(-50%);
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: #ef4444;
    font-size: 16px;
    line-height: 1;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s, background 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
}

.delete-btn:hover {
    background: rgba(239, 68, 68, 0.15);
}

.sidebar-company-card:hover .delete-btn {
    opacity: 1;
}
```

### Change 2: Add the X button to the card template (~line 849)

Insert a `<span>` inside each card `<a>`, after the meta div:

```html
<a href="/results/{{ company.slug }}" class="sidebar-company-card" data-name="{{ company.name|lower }}">
    <div class="sidebar-company-name">{{ company.name }}</div>
    <div class="sidebar-company-meta">
        <span class="sidebar-phase">{{ company.phase }}</span>
        <span class="sidebar-progress">{{ "%.0f"|format(company.progress) }}%</span>
    </div>
    <span class="delete-btn" data-slug="{{ company.slug }}" title="Delete analysis">&times;</span>
</a>
```

### Change 3: Add JavaScript handler (in `HOME_SCRIPTS` string, after the search filter code ~line 959)

```javascript
// Delete analysis handler
document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const slug = this.dataset.slug;
        const card = this.closest('.sidebar-company-card');
        const name = card.querySelector('.sidebar-company-name').textContent;
        if (confirm('Delete analysis for ' + name + '?')) {
            fetch('/api/delete/' + slug, { method: 'DELETE' })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        card.style.transition = 'opacity 0.3s, transform 0.3s';
                        card.style.opacity = '0';
                        card.style.transform = 'translateX(-20px)';
                        setTimeout(() => card.remove(), 300);
                        // Show "No analyses yet" if list is empty
                        const list = document.getElementById('sidebar-list');
                        if (!list.querySelector('.sidebar-company-card')) {
                            list.innerHTML = '<p class="sidebar-empty">No analyses yet</p>';
                        }
                    }
                });
        }
    });
});
```

### Change 4: Add DELETE API endpoint (~line 1217, before the `/start` route)

```python
@app.route('/api/delete/<company_slug>', methods=['DELETE'])
def delete_analysis(company_slug):
    """Delete a company analysis and all its files."""
    import shutil
    company_dir = OUTPUT_DIR / company_slug
    if not company_dir.exists() or not company_dir.is_dir():
        return jsonify({"success": False, "error": "Analysis not found"}), 404
    # Safety: only delete directories that contain state.json
    if not (company_dir / "state.json").exists():
        return jsonify({"success": False, "error": "Invalid analysis directory"}), 400
    shutil.rmtree(company_dir)
    return jsonify({"success": True})
```

---

## Key Files

| File | What to modify |
|------|---------------|
| `strategy_factory/webapp.py` | All 4 changes (CSS, HTML template, JS, API route) |

## Important Notes

- The webapp uses `render_template_string()` with inline string constants — no separate template files
- CSS lives in a `<style>` block inside `BASE_TEMPLATE` string constant
- HTML content lives in `HOME_CONTENT` string constant (Jinja2 template)
- JavaScript lives in `HOME_SCRIPTS` string constant
- `OUTPUT_DIR` is already imported/defined at module level
- The `jsonify` function is already imported from Flask
- The card click is a plain `<a href>` — the delete button must use `e.stopPropagation()` and `e.preventDefault()` to prevent navigation
- The `shutil` import should go at the top of the file or inside the route function

## Verification

1. Run the webapp: `python -m strategy_factory.webapp`
2. Confirm existing analyses appear in the sidebar
3. Hover over a company card — red X should fade in on the right side
4. Click the card (not the X) — navigates to results normally
5. Click the X — confirm dialog appears with company name
6. Confirm deletion — card fades out, directory removed from `output/`
7. Search filtering still works alongside delete buttons
8. If all cards deleted, "No analyses yet" message appears
