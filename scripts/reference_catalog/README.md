# Reference Catalog Scripts

This folder contains helper scripts for refreshing the curated reference index
in `../../other_repos/index.json`.

## Refresh the catalog

```bash
python3 tradecore/scripts/reference_catalog/refresh_other_repos_index.py
```

Useful flags:

- `--max-projects 100` keeps the catalog capped at the requested size.
- `--search-limit 100` asks GitHub for the top 100 matches per query.
- `--offline` rebuilds the catalog from the existing `other_repos/index.json` only.
- `--clone-top 5` optionally clones the first five remote-only repos into `other_repos/`.
- `--github-token $GITHUB_TOKEN` or `GH_TOKEN` improves API limits.

The script uses GitHub search results to discover new reference projects,
preserves existing local references already captured in `other_repos/index.json`,
and writes a single merged JSON catalog that is easy for AI agents to inspect.
