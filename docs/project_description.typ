#set document(
  title: [OANDA TradeCore project description and objectives],
)

#title()

#outline()

= Description
OANDA TradeCore is a modular Python trading system for OANDA that keeps market data, strategy logic, risk checks, execution, monitoring, and the dashboard separated into clear modules.

= Main Objectives

- build a paper-first trading bot that can interact with the OANDA API
- keep broker-specific integration isolated from the rest of the application
- implement reusable strategy modules that can be tested independently
- add risk management and trade safety checks before execution
- support backtesting and paper trading before any live use
- provide a friendly dashboard for monitoring performance and activity
- keep research notes and reference-project findings separate from runtime code
- make the codebase maintainable, modular, and easy to extend

= Initial Module Map

- `src/tradecore/adapters/oanda/` for the OANDA API integration layer
- `src/tradecore/market_data/` for data ingestion and market-state handling
- `src/tradecore/strategies/` for strategy implementations
- `src/tradecore/risk/` for position sizing and safety checks
- `src/tradecore/execution/` for order placement and trade lifecycle handling
- `src/tradecore/monitoring/` for logs, metrics, and runtime status
- `apps/dashboard/` for the user-facing GUI
- `research/` for extracted ideas, comparisons, and notes from reference repos

