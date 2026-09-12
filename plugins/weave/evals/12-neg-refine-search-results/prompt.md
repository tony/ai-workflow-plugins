---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
Our product search page returns way too many irrelevant items for broad queries. Refine the search results by adding a relevance-score threshold and truncating anything below it before we render the list. Where in the search service should that filtering logic live?
