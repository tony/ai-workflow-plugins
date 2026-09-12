---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
The aws provider constraint in our terraform config is way behind, move it up. Here's what we have:

```hcl
# versions.tf (root module)
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.60.0"
    }
  }
}
```

```hcl
# modules/network/versions.tf (child module)
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.55.0"
    }
  }
}
```
