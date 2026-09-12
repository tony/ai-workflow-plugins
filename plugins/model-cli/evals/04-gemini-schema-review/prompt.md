---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/model-cli:gemini "does dropping this field break existing consumers?" timeout:120

```json
{
  "order_id": "string",
  "status": "string",
  "legacy_region_code": "string"
}
```

I'm about to drop legacy_region_code from the response.
