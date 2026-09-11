---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
This branch has one big commit doing five things: it adds a rate limiter, refactors the request logger, fixes a flaky retry, updates the README, and bumps a dependency, all mashed into a single "wip stuff" commit. Rebuild the branch history so each concern is its own reviewable commit, keeping the exact same end result.
