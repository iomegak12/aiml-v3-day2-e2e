# Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `uv: command not found` | uv not installed | Install uv: <https://docs.astral.sh/uv/getting-started/installation/> |
| `ModuleNotFoundError` on run | Dependencies not synced | `uv sync` |
| `ModuleNotFoundError: netcore_tac` | Package not installed in venv | `uv sync` (installs `src/netcore_tac` in editable mode) |
| `ModuleNotFoundError: matplotlib` / `seaborn` in the notebook | `notebook` dependency group not installed | `uv sync` (default groups include `notebook`); never use `--no-default-groups` locally |
| `pytest` collects 0 tests | No test files yet | Add `tests/test_*.py` files |
| Log: `Model file not found: models/eta_model.joblib`; `/ready` → 503; predictions → 503 | Model not trained, or the API started from another folder | `uv run python scripts/train_model.py`, start uvicorn from `day2/`, or set absolute `MODEL_PATH` / `MODEL_METADATA_PATH` |
| `[Errno 10048]` / `address already in use` | Port 8000 taken (another uvicorn or container) | Stop the other process, or `--port 8001` (locally) / `PORT=8001` in `.env` (Compose) |
| `429 Too Many Requests` with `Retry-After` | More than `RATE_LIMIT_REQUESTS` in `RATE_LIMIT_WINDOW_SECONDS` from one IP | Wait `Retry-After` seconds (30 at the start); raise the limits in `.env` for load tests |
| All clients share one rate limit behind a proxy | Every request appears to come from the proxy IP | Set `TRUST_PROXY_HEADERS=true` only behind a trusted proxy that sets `X-Forwarded-For` |
| `ConfigurationError: Invalid configuration …` at startup | A `.env` / environment value is invalid (e.g. `PORT=abc`, `APP_ENV=staging`) | Fix the variable named in the message; see `.env.example` |
| Docker build: `ERROR: models/eta_model.joblib or models/eta_model.json not found` | The model is baked into the image and has not been trained | `uv run python scripts/train_model.py`, then `docker compose up --build` |
| Docker: `failed to connect to the docker API … dockerDesktopLinuxEngine` | Docker Desktop not running | Start Docker Desktop and wait until the engine is running |
| Docker build fails installing a package that was just added | `requirements.lock` is stale | `uv export --frozen --no-default-groups --no-emit-project -o requirements.lock`, then rebuild |
| `UnicodeEncodeError` printing `R²` / `−` on Windows | Console code page is not UTF-8 | `set PYTHONIOENCODING=utf-8` (or `$env:PYTHONIOENCODING="utf-8"` in PowerShell) |
| `make: command not found` / `'make' is not recognized` | GNU Make not installed | Windows: `choco install make` (or `winget install GnuWin32.Make`); macOS: `xcode-select --install` |
| `make predict`: `curl: (7) Failed to connect` | Container not running, or published on another port | `make start`; `make status`; use `make predict PORT=<port>` if `PORT` differs |
| `make predict`: `curl: (22) … 503` | Container up but model not loaded | `make logs`; rebuild with `make train build start` |
| `Makefile:…: *** missing separator` | Recipe lines indented with spaces instead of a tab | Indent recipe lines with a single tab |

> Add a row whenever a new issue and its fix are found.
