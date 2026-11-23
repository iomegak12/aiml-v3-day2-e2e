# Contributing

## Workflow

1. Create a branch from `main`
2. Make changes following [AGENTS.md](AGENTS.md)
3. Add / update pytest unit tests in `tests/`
4. Run `uv run pytest` — all tests must pass
5. Update `README.md` and `CHANGELOG.md`
6. Open a pull request

## Conventions

- Modular code in `src/`
- Reusable scripts in `scripts/`
- Data in `data/`
- Documentation in `docs/`
- Unit tests only (no integration / web tests unless agreed)

## Code of Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
