# Lattice Trade Kit Copilot Instructions

- Read `AGENTS.md` first.
- Use `gh` for GitHub work and keep repo names consistent with `lattice-trade-kit`.
- Keep runtime code in `src/lattice_trade_kit/` and dashboard code in `apps/dashboard/`.
- Default to paper/practice mode unless the user explicitly asks for something else.
- Never store secrets in git.
- Keep private strategy work in `../lattice-trade-kit-private/`.

## Topic instructions

The following files are auto-loaded and contain repo conventions. Read the relevant one when the task matches its topic.

- `.github/instructions/python.instructions.md` — Python 3.12, Poetry, imports
- `.github/instructions/python-tests.instructions.md` — test patterns and pytest usage
- `.github/instructions/git_commit.instructions.md` — commit message format
- `.github/instructions/issue_management.instructions.md` — issue templates and workflow
- `.github/instructions/pull_request.instructions.md` — PR creation and review process
- `.github/instructions/code_review.instructions.md` — code review criteria
- `.github/instructions/debug.instructions.md` — debugging approach
- `.github/instructions/actions.instructions.md` — CI/CD workflow rules
