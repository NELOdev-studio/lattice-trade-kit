#set document(
  title: [Lattice Trade Kit project description and objectives],
)

#title()

#outline()

= Overview
Lattice Trade Kit is a modular Python trading system centered on the OANDA API. The project aims to build a paper-first trading bot that can analyze market conditions, evaluate strategies, manage risk, and execute trades through a cleanly separated broker adapter layer.

= Project Goals

- build a reliable OANDA trading bot that can operate in paper mode before any live deployment
- keep broker integration isolated from strategy, risk, execution, monitoring, and dashboard code
- implement reusable strategy modules that can be tested independently
- support backtesting, paper trading, and iterative refinement
- provide a friendly dashboard for monitoring decisions, performance, and trade activity
- keep research notes and reference-project comparisons separate from runtime code
- make the codebase maintainable, scalable, and easy to extend

= Design Principles

- fail closed when data is missing, a check fails, or market conditions are unsafe
- prefer small, explicit modules over a monolith
- keep strategies pluggable so new ideas can be tested without rewriting the core
- isolate OANDA-specific logic behind an adapter layer so the rest of the system stays portable
- review external code and ideas critically, and reuse them only when licensing and architecture make sense
- keep public code clean, while private ideas and experimental work stay in a separate private workspace

= Non-Functional Requirements

- security: protect credentials, use explicit authentication for dashboards, and avoid storing secrets in git
- reliability: support 24/7 operation with monitoring and clear failure modes
- performance: minimize latency in data processing and execution paths
- maintainability: use modular boundaries, tests, and clear documentation
- portability: keep deployment container-friendly and cloud-ready

= Scope

The first implementation pass should cover:

- OANDA market data ingestion and order execution
- strategy interfaces and at least one reference strategy implementation
- risk checks such as sizing, exposure limits, and safety gates
- backtesting and paper trading
- runtime monitoring and a dashboard
- configuration management for local and example settings

Longer-term extensions may include:

- additional strategies
- richer analytics and reporting
- optional support for other brokers through new adapters
- curated published research notes and reports

= Initial Module Map

- `src/lattice_trade_kit/adapters/oanda/` for the OANDA integration layer
- `src/lattice_trade_kit/core/` for core domain types and orchestration primitives
- `src/lattice_trade_kit/market_data/` for data ingestion and market-state handling
- `src/lattice_trade_kit/strategies/` for strategy implementations
- `src/lattice_trade_kit/risk/` for position sizing and safety checks
- `src/lattice_trade_kit/execution/` for order placement and trade lifecycle handling
- `src/lattice_trade_kit/monitoring/` for logs, metrics, and runtime status
- `src/lattice_trade_kit/ui/` for reusable UI helpers
- `apps/dashboard/` for the user-facing GUI
- `research/` for public-safe notes, comparisons, and source snippets
- `docs/reports/published/` for cleaned reports safe to share in the public repo

= Working With Reference Material
The workspace contains external reference projects and vendor sources. Useful patterns can be adapted after review, but production code should be written to fit Lattice Trade Kit's architecture and licensing requirements.
