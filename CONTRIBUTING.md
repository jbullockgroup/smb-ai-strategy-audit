# Contributing to AI Strategy Factory

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Getting Started

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/ai-strategy-factory.git
   cd ai-strategy-factory
   ```

3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   .\venv\Scripts\activate   # Windows
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Running Tests

```bash
# Run the application locally
python -m strategy_factory.webapp

# Run a dry-run to test without API calls
python -m strategy_factory.main run "Test Company" --dry-run
```

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System info (OS, Python version)
   - Error messages/logs

### Suggesting Features

1. Check existing issues/discussions
2. Create a feature request with:
   - Clear description of the feature
   - Use case and benefits
   - Possible implementation approach

### Submitting Pull Requests

1. Create a branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our code style

3. Test your changes thoroughly

4. Commit with clear messages:
   ```bash
   git commit -m "Add: Brief description of change"
   ```

5. Push and create a PR:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

### Python Guidelines

- Follow PEP 8
- Use type hints where practical
- Add docstrings to functions and classes
- Keep functions focused and small
- Use meaningful variable names

### File Organization

```
strategy_factory/
├── research/      # Phase 1: Data gathering
├── synthesis/     # Phase 2: Document generation
├── generation/    # Phase 3: Final outputs
└── prompts/       # LLM prompt templates
```

### Commit Messages

Use prefixes:
- `Add:` New feature
- `Fix:` Bug fix
- `Update:` Enhancement to existing feature
- `Docs:` Documentation changes
- `Refactor:` Code restructuring
- `Test:` Test additions/changes

## Areas for Contribution

### High Priority

- [ ] **Additional LLM providers** - Add OpenAI, Anthropic support
- [ ] **PDF export** - Generate PDF versions of reports
- [ ] **Improved table handling** - Better markdown table generation
- [ ] **Industry templates** - Specialized prompts for healthcare, finance, etc.

### Medium Priority

- [ ] **Caching** - Cache research results to reduce API calls
- [ ] **Batch processing** - Analyze multiple companies at once
- [ ] **Comparison mode** - Compare AI readiness across companies
- [ ] **Export to Notion/Confluence** - Direct integration

### Good First Issues

- [ ] Add more example prompts
- [ ] Improve error messages
- [ ] Add more unit tests
- [ ] Documentation improvements
- [ ] UI/UX enhancements

## Adding New Deliverables

To add a new deliverable type:

1. Create a prompt file in `strategy_factory/synthesis/prompts/`:
   ```python
   # strategy_factory/synthesis/prompts/new_deliverable.py
   PROMPT = """
   # Task: Generate [Deliverable Name]

   Based on the company research provided, create...

   ## Required Sections
   ...
   """
   ```

2. Register in `strategy_factory/config.py`:
   ```python
   DELIVERABLES = {
       # ... existing deliverables
       "new_deliverable": {
           "name": "New Deliverable Name",
           "format": "markdown",
           "prompt_module": "new_deliverable",
           "order": 16,
       },
   }
   ```

3. Add to orchestrator if needed

## Questions?

- Open a GitHub Discussion for general questions
- Create an Issue for bugs or feature requests
- Tag maintainers for urgent items

Thank you for contributing!
