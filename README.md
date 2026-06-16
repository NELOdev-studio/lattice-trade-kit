# OANDA TradeCore

`tradecore/` is the actual project repo for the new modular OANDA trading system.
Reference repositories stay outside this tree in `../other_repos/` and are treated as read-only study material.

## Working layout

- `src/tradecore/`: core application package
- `apps/dashboard/`: GUI entrypoint and UI-specific code
- `configs/`: committed examples plus local untracked settings
- `data/`: generated caches, backtests, logs, and market snapshots
- `docs/`: project description and architecture notes
- `research/`: extracted ideas, comparisons, and source notes
- `scripts/`: helper scripts
- `deploy/`: container and cloud deployment files
- `vendor/`: explicitly vendored third-party code

The first implementation pass should stay paper-first and keep broker-specific logic inside `src/tradecore/adapters/oanda/`.

## Notes on AI-generated reports

- Keep raw AI outputs, rough drafts, and private strategy analysis in `../tradecore-private/`.
- Promote only cleaned, publishable reports into `docs/reports/published/`.
- Treat everything in this repo as safe to share once the project goes public.
