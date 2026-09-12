---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Normalize the inconsistent spacing in this Tailwind navbar component:

```tsx
<nav className="flex items-center p-4">
  <div className="flex items-center gap-2">
    <a href="/docs">Docs</a>
    <a href="/pricing">Pricing</a>
  </div>
  <div className="ms-3 flex items-center">
    <button className="px-2 h-8">Sign in</button>
    <button className="h-8">Sign up</button>
  </div>
</nav>
```
