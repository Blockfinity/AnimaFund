---
name: deep-learning
description: Perform deep research, build memory, and maintain context awareness.
auto-activate: true
---

1. Research: Use web_search/x_semantic_search/browse_page for in-depth sources (limit: 10-20 results; summarize via code_execution).
2. Memory: Log key insights/summaries in persistent state (SQLite or file: append to learning_log.db with timestamps/context).
3. Context Awareness: Reference past logs/conversations (code_execution: query log for relevant entries). Adapt responses based on history (e.g., "From prior research on [topic]: Update with new data").
4. Evolve: If gaps, self-invoke skill-evolution to integrate new knowledge/tools. Review logs periodically for retention (code_execution: quiz self on facts).
