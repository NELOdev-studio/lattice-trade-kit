# Repo Instructions for Codex

Work inside `tradecore/` unless the user explicitly asks you to operate elsewhere.

## Boundaries

- Treat `../other_repos/` and `../oanda_official_api/` as read-only reference material.
- Do not copy code from reference repos into runtime modules without checking licensing and noting the source in `research/`.
- Keep broker-specific code inside `src/tradecore/adapters/oanda/`.
- Keep strategy code, risk checks, execution, monitoring, and UI separate.

## Safety defaults

- Default to paper/practice mode unless the user explicitly requests something else.
- Never store secrets in git; use `configs/local/` or environment variables.
- Any change that touches risk or execution should be accompanied by tests where practical.

## File placement

- Runtime code belongs in `src/tradecore/`.
- UI entrypoints belong in `apps/dashboard/`.
- Shared docs belong in `docs/`.
- Extracted notes and comparisons belong in `research/`.
- Generated data belongs in `data/` and should stay out of version control.
- Raw AI-generated reports, private strategy drafts, and unreleased analysis belong in `../tradecore-private/`.
- Only sanitized or publishable report outputs should be committed under `docs/reports/published/`.

## Working style

- Prefer small, focused modules.
- Update the docs when the architecture changes.
- Record useful ideas from reference projects in `research/notes/` instead of mixing them into the product code immediately.
