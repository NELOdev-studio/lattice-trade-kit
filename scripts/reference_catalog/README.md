# Reference Catalog Scripts

This folder contains helper scripts for refreshing the curated reference index
in `../../reference_catalog_repo/sources/other_repos/raw_index.json`.

## Refresh the catalog

```bash
python3 lattice-trade-kit/scripts/reference_catalog/refresh_other_repos_index.py
```

Then rebuild the compact catalog repo:

```bash
python3 scripts/reference_catalog/export_reference_catalog_repo.py
```

Useful flags:

- `--max-projects 100` keeps the catalog capped at the requested size.
- `--search-limit 100` asks GitHub for the top 100 matches per query.
- `--offline` rebuilds the raw snapshot from the existing raw index only.
- `--clone-top 5` optionally clones the first five remote-only repos into `other_repos/`.
- `--github-token $GITHUB_TOKEN` or `GH_TOKEN` improves API limits.

The script uses GitHub search results to discover new reference projects,
preserves existing local references already captured in the raw snapshot, and
writes a single merged JSON snapshot. The workspace export script then splits
that snapshot into the versioned catalog repo, one JSON file per project.
