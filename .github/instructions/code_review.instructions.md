# Code Review

- Review for correctness, safety, regressions, and missing tests first.
- Prefer concise findings with file references and concrete impact.
- Call out any change that could affect broker behavior, data freshness, or execution flow.
- If nothing is wrong, say that explicitly and mention residual risks.

Example:

```bash
gh pr review 123 --comment
```
