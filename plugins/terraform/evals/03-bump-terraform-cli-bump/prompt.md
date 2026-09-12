---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/terraform:bump-terraform 1.14.0

Two root modules in this repository pin the CLI:

```hcl
# environments/staging/versions.tf
terraform {
  required_version = "= 1.9.5"
}
```

```hcl
# environments/prod/versions.tf
terraform {
  required_version = "= 1.10.2"
}
```
