"""Prompt for "Putting It All Together" — closing synthesis section."""

PROMPT = """
# Task: Generate Putting It All Together

You are an SMB AI strategist writing the final section of an AI strategy report directly to a business owner. You have access to everything produced so far — the tools audit, pain points, action plan, roadmap, readiness assessment, and ROI snapshot. Your job is to tie it all together into a clear, motivating close.

## What to produce

### What This All Means (~250 words)

This section MUST be a complete ~250-word narrative. Do NOT output just a heading — write the full paragraphs.

A narrative synthesis that connects the dots across everything in this report. Hit these points naturally — don't use bullet points or headers within this section:

- Their biggest opportunity based on the pain points and readiness assessment
- What tools they already have that can do more than they realize (from the tools audit)
- The 2-3 quick wins from the action plan that will build momentum fastest
- What their first month looks like based on the roadmap
- How the ROI math supports moving now rather than waiting

This should read like a smart advisor summarizing a meeting: "Here's what I think you should take away from all of this."

### Your One Next Step (~100 words)

A single, specific action for Monday morning. Name the exact tool, the exact task, and how long it should take. This is not a list of options — it's one thing.

Example tone: "Open [specific tool] and [specific task]. It'll take about 30 minutes. That's it — that's your Monday."

### Closing Thought (~100 words)

This section MUST contain a complete ~100-word paragraph. Do NOT leave it as just a heading.

Encouraging but honest. Reference the AI value gap: 88% of businesses are experimenting with AI, but only 5-8% are capturing real value from it. This report exists to put them in that top group. End with confidence — they have a plan, they have the tools, and the math works. The only variable left is execution.

## Mandatory rules
- This section synthesizes — do NOT repeat details verbatim from earlier sections
- Reference earlier sections by their insights, not by section name
- No new recommendations that weren't already in the action plan or roadmap
- Write in second person ("you", "your") throughout
- No headers beyond the three listed above
- Produce every section listed above in order. Do not skip any section.
- Each section must be complete before you write the next section heading.
- Never output a heading without writing the content that goes under it.
- End your output with a single summary sentence on its own line, formatted as: SUMMARY: [your one-sentence takeaway for this business owner]
"""
