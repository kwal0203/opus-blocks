# AGENTS Instructions

## Tooling
- Use ruff for linting and formatting.
- Use pre-commit for hook management.
- Use mypy or pyright for type checking when helpful.
- Use docker compose for local testing.
- Use terraform fmt and tflint for infrastructure code.
- Never commit the /information directory (already in .gitignore).

## Preferences
- Use uv for Python package management when appropriate.
- Use git for version control.
- Use the GitHub gh CLI for creating pull requests.
- Always add a brief PR summary when creating PRs.
- Do all work on a new branch; never work directly on main.
- Keep local changes minimal and incremental.
