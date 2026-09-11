---
type: llm
---
The reply rewrites the paragraph as a single unwrapped block, or explicitly says a rendered body must not be hard-wrapped like the pasted version, rather than keeping the manual line breaks as-is.
The reply adds a blank line after </summary> inside the details block, or flags the missing blank line as the reason that block would render broken.
The reply flags or replaces the blob/main link with a line anchor, recommending a pinned release tag or commit SHA instead, since a blob/main link points at different code over time.
