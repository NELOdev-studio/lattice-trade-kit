# Codex Instructions

Canonical repo instructions live in [`AGENTS.md`](../AGENTS.md).

Quick defaults:

- Work inside `lattice-trade-kit/` only.
- Treat `../other_repos/` and `../oanda_official_api/` as read-only references.
- Keep `src/lattice_trade_kit/adapters/oanda/` for broker-specific code.
- Put extracted ideas and comparisons in `research/`, not in runtime modules.
- Keep secrets out of git and use `configs/local/` for machine-specific settings.
- Default to paper/practice mode.
- Update tests and docs when behavior changes.
- Keep raw AI-generated reports and private strategy work in `../lattice-trade-kit-private/`.
- Commit only cleaned, public-safe reports into `docs/reports/published/`.
