# Lattice Trade Kit

`lattice-trade-kit/` is the public project repo for the modular OANDA trading system.
Reference repositories stay outside this tree in `../other_repos/` and are treated as read-only study material.

## Working layout

- `src/lattice_trade_kit/`: core application package
- `apps/dashboard/`: GUI entrypoint and UI-specific code
- `configs/`: committed examples plus local untracked settings
- `data/`: generated caches, backtests, logs, and market snapshots
- `docs/`: project description and architecture notes
- `research/`: extracted ideas, comparisons, and source notes
- `scripts/`: helper scripts
- `deploy/`: container and cloud deployment files
- `vendor/`: explicitly vendored third-party code

The first implementation pass should stay paper-first and keep broker-specific logic inside `src/lattice_trade_kit/adapters/oanda/`.

## Notes on AI-generated reports

- Keep raw AI outputs, rough drafts, and private strategy analysis in `../lattice-trade-kit-private/`.
- Promote only cleaned, publishable reports into `docs/reports/published/`.
- Treat everything in this repo as safe to share once the project goes public.
