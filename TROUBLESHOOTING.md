# Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `uv: command not found` | uv not installed | Install uv: <https://docs.astral.sh/uv/getting-started/installation/> |
| `ModuleNotFoundError` on run | Dependencies not synced | `uv sync` |
| `ModuleNotFoundError: netcore_tac` | Package not installed in venv | `uv sync` (installs `src/netcore_tac` in editable mode) |
| `pytest` collects 0 tests | No test files yet | Add `tests/test_*.py` files |

> Add a row whenever a new issue and its fix are found.
