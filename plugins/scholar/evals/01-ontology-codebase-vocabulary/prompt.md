---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Distil an ontology of what this codebase calls things. Here's the module I'm starting from:

```python
class PortAdapter:
    """Wraps a third-party client behind the port interface."""

class EventBus:
    """Publishes domain events to subscribed handlers."""

def dispatch_handler(event, handler):
    handler.handle(event)
```

What types and vocabulary does this code actually use for its own concepts?
