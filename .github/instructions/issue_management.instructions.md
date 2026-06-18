# Issue Management

- Treat GitHub issues and milestones as the remote source of truth.
- Mirror planning context locally in `docs/dev/issues/`.
- Use the project labels from `docs/dev/github_labels.json`.
- Keep generated mirrors out of hand-edited workflows.

Examples:

```bash
gh issue create --title "Add dashboard scaffold" --label "type/feature" --label "area/dashboard"
gh issue list --state open
gh api repos/NELOdev-studio/lattice-trade-kit/milestones
```
