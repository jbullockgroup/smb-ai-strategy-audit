# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SMB AI Strategy Audit generates practical AI adoption strategy deliverables for small-to-midsize businesses using Perplexity AI for research and Google Gemini for document synthesis.

**What it produces:**
- 8 strategic markdown documents (including Executive Summary)
- 1 Word document (combined strategy report)
- 1 PDF (combined strategy report)

## Quick Commands

### Setup (First Time)
```bash
# Option 1: Automated setup
python setup.py

# Option 2: Manual setup
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OR: .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Run the Web App
```bash
source venv/bin/activate  # macOS/Linux
python -m strategy_factory.webapp
# Opens http://localhost:8888 automatically
```

### Run via CLI
```bash
# Full pipeline for a company
python -m strategy_factory.main run "Company Name"

# With additional context
python -m strategy_factory.main run "Acme Corp" --context "plumbing, 25 employees"

# With audience profile for regional/cultural tailoring
python -m strategy_factory.main run "Company Name" --audience mountain_bizworks_scaleup

# Dry run (no API calls)
python -m strategy_factory.main run "Company Name" --dry-run

# Skip individual phases
python -m strategy_factory.main run "Company Name" --skip-research
python -m strategy_factory.main run "Company Name" --skip-synthesis
python -m strategy_factory.main run "Company Name" --skip-generation

# Check status of existing analysis
python -m strategy_factory.main status "Company Name"

# Resume interrupted pipeline
python -m strategy_factory.main resume "Company Name"

# List all companies with progress
python -m strategy_factory.main list

# Reset progress and start fresh
python -m strategy_factory.main reset "Company Name"
```

## Architecture

```
strategy_factory/
├── main.py              # CLI entry point
├── webapp.py            # Flask web application (primary UI)
├── server.py            # Simple static viewer for completed outputs
├── config.py            # Configuration & deliverable definitions
├── models.py            # Pydantic data models
├── progress_tracker.py  # State management
├── knowledge_loader.py  # Knowledge base guide loading for context
├── audience_loader.py   # Audience profile loading for regional tailoring
├── logo_extractor.py    # Company logo extraction from website
├── temporal.py          # Date/time context for queries
├── research/            # Phase 1: Perplexity research
│   ├── orchestrator.py
│   ├── perplexity_client.py
│   ├── query_templates.py   # Structured query templates
│   └── result_processor.py  # Tier detection & output building
├── synthesis/           # Phase 2: Gemini document generation
│   ├── orchestrator.py
│   ├── gemini_client.py
│   ├── context_builder.py   # Builds prompts with research + guides
│   └── prompts/             # 8 deliverable prompt templates
└── generation/          # Phase 3: Final outputs
    ├── orchestrator.py
    ├── markdown_generator.py
    ├── docx_generator.py
    └── pdf_generator.py
```

## Pipeline Flow

1. **Research Phase** → Perplexity API
   - Company Discovery: online presence, reviews, sales channels
   - Industry Analysis: overview, challenges, tools, operations
   - AI Opportunity: examples, tools, trends
   - 13 queries: Industry detection, company discovery, industry analysis, AI opportunity

2. **Synthesis Phase** → Gemini API (gemini-2.5-flash)
   - 8 markdown deliverables generated in dependency order:
     1. Where You Stand Today (no dependencies)
     2. Where You're Losing Money (no dependencies)
     3. Your AI Readiness (depends on 01, 02)
     4. What To Do First (depends on 02)
     5. Your Week-by-Week Plan (depends on 03)
     6. What It Costs & What You Save (depends on 03)
     7. Putting It All Together (depends on 01–06)
     8. Executive Summary (depends on all above)

3. **Generation Phase** → Local
   - Markdown files saved to disk
   - Combined DOCX strategy report
   - Combined PDF strategy report

## Deliverables

| ID | Name | Format | Dependencies |
|----|------|--------|-------------|
| 01_tools_audit | Where You Stand Today | markdown | — |
| 02_daily_pain_points | Where You're Losing Money | markdown | — |
| 03_action_plan | What To Do First | markdown | 02 |
| 04_simple_roadmap | Your Week-by-Week Plan | markdown | 03 |
| 05_readiness_assessment | Your AI Readiness | markdown | 01, 02 |
| 06_roi_snapshot | What It Costs & What You Save | markdown | 03 |
| 07_closing | Putting It All Together | markdown | all above |
| 08_executive_summary | Executive Summary | markdown | all above |
| final_strategy_report | AI Strategy Report | docx | ALL_MARKDOWN |
| final_strategy_report_pdf | AI Strategy Report (PDF) | pdf | ALL_MARKDOWN |

## Environment Variables

Required in `.env`:
```
PERPLEXITY_API_KEY=pplx-xxx
GEMINI_API_KEY=AIzaSyxxx
```

## Output Structure

```
output/{company-slug}/
├── markdown/              # 8 .md files
├── documents/             # .docx and .pdf strategy reports
├── research_cache.json    # Raw research data
└── state.json             # Progress tracking
```

## Key Files for Development

- `config.py` - Deliverable definitions, API models, retry config
- `synthesis/prompts/*.py` - 8 deliverable prompt templates
- `research/query_templates.py` - Perplexity query templates by phase
- `knowledge_loader.py` - Loads knowledge base guides for synthesis context
- `audience_loader.py` - Loads audience profiles from `knowledge_base/audience/`
- `webapp.py` - Web UI (primary interface)
- `server.py` - Simple viewer for completed outputs (`python -m strategy_factory.server "slug"`)

## Troubleshooting

**Port in use:** App auto-finds available port, or use `--port 9000`

**Missing API keys:** Check `.env` file exists and has valid keys

## Cost Estimates

-  ~$0.15 per company

