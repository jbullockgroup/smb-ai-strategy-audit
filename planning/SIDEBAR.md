# Sidebar Plan: Move Previous Analyses to Left Sidebar with Search

## Context

The home page currently shows a "Previous Analyses" card **below** the main setup form. The user wants it moved to a **left sidebar** so the form stays centered as the primary action, with a search box at the top of the sidebar to filter analyses by name.

Additionally, the user wants company names displayed in their **original form** (e.g., "Black Mountain Yarn Shop"), not kebab-case (e.g., "black-mountain-yarn-shop"). The good news: the data layer already stores the original name — no backend changes needed.

## Single file to modify

**`strategy_factory/webapp.py`** — all templates and CSS are inline in this file. No other files need changes.

---

## Current State (what to change)

### BASE_TEMPLATE (line 50–737)

**CSS to ADD** (insert before the closing `</style>` tag around line 717):

```css
/* Home page sidebar layout */
.home-layout {
    display: flex;
    gap: 2rem;
    min-height: calc(100vh - 200px);
}

.analyses-sidebar {
    width: 280px;
    flex-shrink: 0;
    background: var(--card);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    height: fit-content;
    position: sticky;
    top: 1rem;
}

.analyses-sidebar h3 {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

.sidebar-search {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 0.875rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.15s, box-shadow 0.15s;
}

.sidebar-search:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-light);
}

.sidebar-list {
    max-height: calc(100vh - 350px);
    overflow-y: auto;
}

.sidebar-company-card {
    display: block;
    padding: 0.75rem;
    border-radius: 6px;
    text-decoration: none;
    color: var(--text);
    transition: background 0.15s;
    border-bottom: 1px solid var(--border);
}

.sidebar-company-card:last-child {
    border-bottom: none;
}

.sidebar-company-card:hover {
    background: var(--bg);
}

.sidebar-company-name {
    font-weight: 500;
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.sidebar-company-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.sidebar-phase {
    text-transform: capitalize;
}

.sidebar-progress {
    font-weight: 600;
    color: var(--success);
}

.sidebar-empty {
    color: var(--text-secondary);
    font-size: 0.875rem;
    text-align: center;
    padding: 1rem;
}

.home-main {
    flex: 1;
    min-width: 0;
}
```

Also add a responsive rule inside the **existing** `@media (max-width: 900px)` block (line 708):

```css
.home-layout {
    flex-direction: column;
}

.analyses-sidebar {
    width: 100%;
    position: relative;
    top: 0;
    order: 2;
}

.home-main {
    order: 1;
}
```

### CSS to REMOVE

The old `.companies-list` (line 660–663) and `.company-card` (line 665–681) and `.company-info` (line 683–692) and `.company-meta` (line 694–706) styles are no longer used on the home page. However, check if they're used elsewhere before removing — they appear to be home-page-only, so they can be removed or left as dead CSS (removing is cleaner).

---

### HOME_CONTENT (line 739–833)

**Replace the entire HOME_CONTENT** with a new version that wraps everything in `.home-layout`:

```html
<div class="home-layout">
    <aside class="analyses-sidebar">
        <h3>Previous Analyses</h3>
        <input type="text" class="sidebar-search" placeholder="Search analyses..." id="sidebar-search">
        <div class="sidebar-list" id="sidebar-list">
            {% for company in companies %}
            <a href="/results/{{ company.slug }}" class="sidebar-company-card" data-name="{{ company.name|lower }}">
                <div class="sidebar-company-name">{{ company.name }}</div>
                <div class="sidebar-company-meta">
                    <span class="sidebar-phase">{{ company.phase }}</span>
                    <span class="sidebar-progress">{{ "%.0f"|format(company.progress) }}%</span>
                </div>
            </a>
            {% endfor %}
            {% if not companies %}
            <p class="sidebar-empty">No analyses yet</p>
            {% endif %}
        </div>
    </aside>

    <div class="home-main">
        <div style="max-width: 700px; margin: 0 auto;">
            <div class="card">
                <!-- EXISTING FORM GOES HERE — the entire <form id="analysis-form">...</form> block, unchanged -->
            </div>
        </div>
    </div>
</div>
```

Key changes:
- Remove the outer `<div style="max-width: 700px; margin: 2rem auto;">` wrapper
- Add `.home-layout` flex container
- Move the previous analyses into `<aside class="analyses-sidebar">`
- Wrap the form in `<div class="home-main"><div style="max-width: 700px; margin: 0 auto;">`
- **Delete** the old `{% if companies %}...{% endif %}` block (lines 814–832)
- The sidebar always shows (even when empty, it shows "No analyses yet")

---

### HOME_SCRIPTS (line 836–913)

**Add** the search filtering JS at the beginning of the `<script>` block (after line 837), before the existing radio-option code:

```javascript
// Sidebar search filtering
const searchInput = document.getElementById('sidebar-search');
const sidebarList = document.getElementById('sidebar-list');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        sidebarList.querySelectorAll('.sidebar-company-card').forEach(card => {
            const name = card.dataset.name;
            card.style.display = name.includes(query) ? '' : 'none';
        });
    });
}
```

---

## Company Name Display

The user specifically asked for company names to show in their original form (not kebab-case). The data already handles this correctly:

- **`ProgressTracker.__init__`** stores `self.company_name` as the original name passed in
- **`get_progress_summary()`** returns `"company_name": self.company_name` (original form)
- **The `home()` route** (line 1069) sets `"name": summary["company_name"]` — this is the original name
- **In the template**, `{{ company.name }}` renders the original name

So the display name is already correct. The `data-name="{{ company.name|lower }}"` attribute is only for case-insensitive search matching. No backend changes needed.

If the user is seeing kebab-case names, it would be because the original company name was entered in kebab-case. That's a data entry issue, not a code issue.

---

## Route Changes

**None.** The `home()` route (line 1057–1091) already passes the correct data. No Python code changes needed.

---

## Verification Steps

1. `source venv/bin/activate && python -m strategy_factory.webapp`
2. Open http://localhost:8888
3. Verify: Left sidebar shows with "Previous Analyses" heading and search box
4. Verify: Form is centered in the main area to the right
5. Verify: Company names display in proper case (e.g., "Black Mountain Yarn Shop", not "black-mountain-yarn-shop")
6. Verify: Typing in the search box filters the list in real-time
7. Verify: Clicking a company card navigates to `/results/{slug}`
8. Verify: On narrow screens (<900px), sidebar stacks below the form
9. Verify: Empty state shows "No analyses yet" when no previous analyses exist
10. Verify: Other pages (results, progress, audience builder) are unaffected
