# Repo Instructions for Codex

Work inside `lattice-trade-kit/` unless the user explicitly asks you to operate elsewhere.

## Boundaries

- Treat `../other_repos/` and `../oanda_official_api/` as read-only reference material.
- Do not copy code from reference repos into runtime modules without checking licensing and noting the source in `research/`.
- Keep broker-specific code inside `src/lattice_trade_kit/adapters/oanda/`.
- Keep strategy code, risk checks, execution, monitoring, and UI separate.
- Keep public-safe research and cleaned reports in this repo.
- Keep raw AI outputs, private strategy work, and unreleased analysis in `../lattice-trade-kit-private/`.

## Safety defaults

- Default to paper/practice mode unless the user explicitly requests something else.
- Never store secrets in git; use `configs/local/` or environment variables.
- Any change that touches risk or execution should be accompanied by tests where practical.

## File placement

- Runtime code belongs in `src/lattice_trade_kit/`.
- UI entrypoints belong in `apps/dashboard/`.
- Shared docs belong in `docs/`.
- Generated GitHub issue mirrors belong in `docs/dev/issues/mirrored_from_github/`.
- Local-only issue drafts belong in `docs/dev/issues/drafts/`.
- Raw issue sync snapshots and sync state belong in `docs/dev/issues/_source/`.
- Extracted notes and comparisons belong in `research/`.
- Generated data belongs in `data/` and should stay out of version control.
- Raw AI-generated reports, private strategy drafts, and unreleased analysis belong in `../lattice-trade-kit-private/`.
- Only sanitized or publishable report outputs should be committed under `docs/reports/published/`.

## Working style

- Prefer small, focused modules.
- Update the docs when the architecture changes.
- Record useful ideas from reference projects in `research/notes/` instead of mixing them into the product code immediately.
- Do not hand-edit generated issue mirrors; regenerate them from the raw `_source/` snapshots instead.
