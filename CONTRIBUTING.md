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
| Run API + web UI in Docker | `make start` (open <http://localhost>) |
| Rebuild only the web UI | `make build-web start` |
| Run the tests | `uv run pytest` and `make test-web` |
| Refresh the Docker lock file | `uv export --frozen --no-default-groups --no-emit-project -o requirements.lock` |
| Shortcuts for all of the above | `make help` (build, build-api, build-web, start, stop, predict, status, logs, train, test, test-web, lock) |

- Add runtime dependencies with `uv add <pkg>`; notebook-only ones with `uv add --group notebook <pkg>`
- After any dependency change, refresh and commit `requirements.lock`
- Keep training and serving logic in `src/netcore_tac/` (`cleaning.py`, `features.py`, `model.py`) — never copy it into the API or scripts

## Web UI (`web/`)

- Edit `web/site/` (HTML, CSS, JS) and `web/nginx/`; rebuild with `make build-web start`
- **Logic goes in pure modules** (`config`, `payload`, `chips`, `eta`, `api`, `history`, `theme`, `markdown`) that take clock, storage, fetch or document as parameters, each with a `tests/web/<module>.test.mjs` (`node:test`, no npm packages)
- **Agreed exception to the unit-test rule:** the page scripts `layout.js`, `home.js`, `register.js` and `theme-init.js` are thin DOM glue and have no unit tests (that would need jsdom); keep them free of business logic and check them through the acceptance steps in `docs/prompts/002-web-ui-prompt.md`
- **CSP:** no inline `<script>`, no `on*=` attributes, no `style="…"`; put code in `js/` and styles in `css/`
- **Colours:** use only the tokens in `css/tokens.css` (NetCore light and dark); keep WCAG AA contrast (check with `docs/design/theme-options.html`)
- Keep `config.js` (`FIELD_LIMITS`, `ENUMS`) in sync with `TicketIn` in `src/netcore_tac/api/schemas.py`
- **Upgrading `marked`:** `npm pack marked@<version>`, copy `package/lib/marked.esm.js` to `web/site/vendor/` (drop the `//# sourceMappingURL` line) and `package/LICENSE` to `vendor/marked.LICENSE`; pick a release at least two weeks old; run `make test-web`; update the version in README and SECURITY

## Conventions

- Modular code in `src/`
- Reusable scripts in `scripts/`
- Data in `data/`; trained model artefacts in `models/` (git-ignored)
- Documentation in `docs/`
- Unit tests only (no integration / web tests unless agreed)

## Code of Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
