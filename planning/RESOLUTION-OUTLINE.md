# Resolution Outline

Generated 2026-04-04 from user feedback session.

---

## Phase 1: Remove Features from Workflow

- [ ] 1. Skip diagram generation — Remove from `generation/orchestrator.py` pipeline
- [ ] 2. Skip PPTX generation — Remove from `generation/orchestrator.py` pipeline
- [ ] 3. Update webapp sidebar — Remove "Diagrams" and "Presentations" sections from `webapp.py`
- [ ] 4. Update stats bar — Remove the "Diagrams" stat from the results page header

---

## Phase 2: Rewrite All 6 Prompts + Add Closing Section

- [ ] 5. **`tech_inventory.py`** — Add fallback instructions: if research returns nothing about tools, infer based on industry/size. Mention Cowork as a tool that can audit their own files.
- [ ] 6. **`pain_points.py`** — Rename "The 5 Boring Workflows" to "Your Highest-Impact Workflows". Fix "Content Creation Gap" to always produce substantive content. Emphasize content creation as an easy win.
- [ ] 7. **`quick_wins.py`** — Add Claude Cowork as recommended tool (for owners who want autonomous multi-step work). Update tool preferences section to reflect 2026 landscape.
- [ ] 8. **`roadmap.py`** — Ensure references to tools are current. Consider Cowork integration in the 30-day plan.
- [ ] 9. **`maturity_assessment.py`** — Change scoring from 0-3 to 1-5 per question (total /25). Update score interpretation tiers.
- [ ] 10. **`roi_calculator.py`** — Update tool names/pricing. Include Cowork as a tier option.
- [ ] 11. **New: `closing.py`** — "Putting It All Together" narrative synthesis (Option B). Connects the dots between all sections, tells the story of this specific business, ends with encouraging but honest closer.

---

## Phase 3: Update Configuration & Orchestrator

- [ ] 12. **`config.py`** — Add new closing section deliverable. Update `tldr_guides` mappings to use new SMB guides.
- [ ] 13. **`synthesis/orchestrator.py`** — Add closing section to generation order. Update system instruction with Claude Cowork and 2026 tool references.
- [ ] 14. **`synthesis/prompts/__init__.py`** — Register new closing prompt.

---

## Phase 4: Fix Content Completeness

- [ ] 15. **Investigate truncation** — Check Gemini client settings (max output tokens) and DOCX generator to find where sections get cut off. Increase token limits if needed.
- [ ] 16. **Add completeness instructions** — Every prompt should include "Every section must end with a complete sentence. Never truncate."
- [ ] 17. **Increase word count targets** — Bump major sections to 500-800 words to hit 15-20 page target.

---

## Phase 5: Test

- [ ] 18. **Dry run** — Verify the pipeline runs without diagrams/presentations
- [ ] 19. **Live run** — Test with a sample company and check PDF output for completeness, length, and content quality

---

## Key Decisions

| Topic | Decision |
|-------|----------|
| Closing section | Option B: "Putting It All Together" — narrative synthesis |
| Prompt rewrite scope | All 6 prompts at once, not incremental |
| Content Creation Gap | Keep as standalone section, fix to always produce content |
| Readiness scoring | 1-5 per question, total out of 25 (was 0-3 out of 15) |
| Claude Cowork | Recommend prominently — agentic tool for non-technical SMB owners, Max plan ($100-200/mo) |
| Diagrams | Remove from workflow and sidebar, keep script |
| Presentations | Remove from workflow and sidebar, keep script |
| Target page length | 15-20 pages (was ~12) |
