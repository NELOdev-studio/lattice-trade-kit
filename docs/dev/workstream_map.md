# Workstream Map

| Workstream | Module Path | Area Label | Notes |
| --- | --- | --- | --- |
| OANDA adapter | `src/lattice_trade_kit/adapters/oanda/` | `area/adapter` | Broker contract, request models, and response parsing. |
| Market data | `src/lattice_trade_kit/market_data/` | `area/market-data` | Backfill, storage, freshness, and scheduling. |
| Strategies | `src/lattice_trade_kit/strategies/` | `area/strategies` | Signal generation and registry. |
| Risk | `src/lattice_trade_kit/risk/` | `area/risk` | Fail-closed gates, sizing, and exposure. |
| Execution | `src/lattice_trade_kit/execution/` | `area/execution` | Paper/live routing and execution receipts. |
| Monitoring | `src/lattice_trade_kit/monitoring/` | `area/monitoring` | Decision logs, metrics, and health. |
| Dashboard | `apps/dashboard/` | `area/dashboard` | Operator console and review surface. |
| Backtesting | `src/lattice_trade_kit/backtesting/` | `area/backtesting` | Replay, metrics, and report generation. |
| Private research | `../lattice-trade-kit-private/` | `area/research` | Proprietary analysis, tuning, and report drafts. |
