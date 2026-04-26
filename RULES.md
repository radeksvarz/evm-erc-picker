# Project Rules

Mandatory rules for AI coding assistants working on this project.

## Rules

1. **Constant Changes**: You have to always explicitly ask when changing any constant (e.g., URLs, timeouts, file paths).
2. **Language**: All code files, variable names, function names, and comments MUST be in **English**.
3. **Dependencies**: ALWAYS ask the user before adding any new dependencies to the project!
4. **Testing**: All new logic must include automated tests. Aim for 100% coverage where reasonable (e.g., config and logic layers). Use `uv run pytest` for testing.
5. **Code Style**: Use `uv run ruff check --fix .` and `uv run ruff format .` to maintain code quality and consistency.
