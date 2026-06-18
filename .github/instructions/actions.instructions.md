# GitHub Actions

- Keep workflow files small and explicit.
- Use GitHub Actions for CI checks, not hidden local-only steps.
- Keep secrets in GitHub Secrets, never in the repository.
- When a workflow fails, inspect the run before editing the workflow.

Examples:

```bash
gh run list
gh run view --log
```
