# Plan: Reduce Claude Max Overemphasis & Fix Pricing

## Context

Claude Max appears in tool recommendations with `$100-200/mo` pricing and is overemphasized in generated strategy reports. The system instruction tells Gemini to recommend Claude Max as the universal #1 pick across all 7 deliverables. The goal: keep Claude Cowork as the "one thing" recommendation but default to Pro ($20/mo) with Max ($100/mo) as a situational upgrade, and remove Claude Max from mandatory tool lists.

## What This Codebase Does

AI Strategy Factory generates AI adoption strategy reports for small-to-midsize businesses. It uses Perplexity for research and Gemini for document synthesis. The synthesis phase generates 7 markdown deliverables, each prompted with a system instruction from `orchestrator.py` and per-deliverable prompts from `synthesis/prompts/`.

## Files to Modify (2 files, 3 edits)

### 1. `strategy_factory/synthesis/orchestrator.py` — line 227

This is the **system instruction sent to Gemini for every deliverable**. It's the biggest driver of overemphasis.

**Current (line 227):**
```
- If the business could only do ONE thing: recommend Claude Cowork (Max plan, $100-200/mo) — it's an agentic AI that handles multi-step work autonomously, perfect for non-technical owners
```

**Replace with:**
```
- If the business could only do ONE thing: recommend Claude Cowork — Pro plan ($20/mo) for most owners, or Max plan ($100/mo) if they need autonomous multi-step work like analyzing files, managing complex tasks, or acting as an ongoing AI partner
```

### 2. `strategy_factory/synthesis/prompts/quick_wins.py` — lines 35-36

This prompt generates the "What To Do First" action plan deliverable. Lines 35-36 have two separate Claude bullets, which gives Claude 2 of 7 tool rec slots (29%).

**Current (lines 35-36):**
```
- **Claude Pro ($20/mo)** — long documents, proposals, complex writing, document analysis
- **Claude Max ($100-200/mo)** — for owners who want an AI partner that can handle multi-step work autonomously, analyze files, and manage complex tasks
```

**Replace with:**
```
- **Claude Pro ($20/mo)** — long documents, proposals, complex writing, document analysis. For owners who want an AI partner that handles multi-step work autonomously, the Max plan ($100/mo) is available.
```

### 3. `strategy_factory/synthesis/prompts/quick_wins.py` — line 64

This is the mandatory tools list that forces Gemini to use specific tools in action tables.

**Current (line 64):**
```
- **Use these tools:** ChatGPT Plus ($20/mo), Claude Pro ($20/mo), Claude Max ($100-200/mo), Gemini ($0-20/mo), Perplexity ($20/mo), n8n for automation, native integrations first
```

**Replace with:**
```
- **Use these tools:** ChatGPT Plus ($20/mo), Claude Pro ($20/mo), Gemini ($0-20/mo), Perplexity ($20/mo), n8n for automation, native integrations first
```

## Verification

1. `grep -ri "Max plan" strategy_factory/` — should show exactly two references (orchestrator.py and quick_wins.py), both with `$100/mo`
2. `grep -ri "Claude Max" strategy_factory/` — should return no results
3. `grep -r '\$200' strategy_factory/synthesis/` — should return no results
4. `python -m strategy_factory.main run "Test Co" --dry-run` — confirm no runtime errors

## Effect of These Changes

- Claude Cowork remains the "if you could only do one thing" pick, but defaults to $20 Pro plan
- Max ($100/mo) is mentioned as a situational upgrade, not the default
- Claude Max disappears from the mandatory tools list, so Gemini won't force it into every action table row
- Claude goes from 2 dedicated tool-rec bullets down to 1, reducing perceived bias
- Price changes from `$100-200/mo` to `$100/mo` everywhere
