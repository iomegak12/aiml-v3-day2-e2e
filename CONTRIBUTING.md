# Contributing

## Workflow

1. Create a branch from `main`
2. Make changes following [AGENTS.md](AGENTS.md)
3. Add / update pytest unit tests in `tests/`
4. Run `uv run pytest` — all tests must pass
5. Update `README.md` and `CHANGELOG.md`
6. Open a pull request

## Common Tasks

| Task | Command |
|------|---------|
| Install everything | `uv sync` |
| Generate the dataset | `uv run python scripts/generate_tickets.py --n 5000 --seed 42` |
| Train the model | `uv run python scripts/train_model.py` |
| Run the API | `uv run uvicorn netcore_tac.api.main:app --no-proxy-headers` (from `day2/`) |
| Run the API in Docker | `docker compose up --build` |
| Run the tests | `uv run pytest` |
| Refresh the Docker lock file | `uv export --frozen --no-default-groups --no-emit-project -o requirements.lock` |
| Shortcuts for all of the above | `make help` (build, start, stop, predict, status, logs, train, test, lock) |

- Add runtime dependencies with `uv add <pkg>`; notebook-only ones with `uv add --group notebook <pkg>`
- After any dependency change, refresh and commit `requirements.lock`
- Keep training and serving logic in `src/netcore_tac/` (`cleaning.py`, `features.py`, `model.py`) — never copy it into the API or scripts

## Conventions

- Modular code in `src/`
- Reusable scripts in `scripts/`
- Data in `data/`; trained model artefacts in `models/` (git-ignored)
- Documentation in `docs/`
- Unit tests only (no integration / web tests unless agreed)

## Code of Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
