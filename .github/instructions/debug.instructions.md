# Debugging

- Reproduce the problem before changing code.
- Reduce the case to the smallest failing path.
- Inspect logs, tests, and inputs before guessing.
- Prefer targeted fixes over broad rewrites.

Examples:

```bash
poetry run pytest -k "risk and not integration"
python -m pdb tradecore/scripts/sync_github_issues.py --dry-run
```
