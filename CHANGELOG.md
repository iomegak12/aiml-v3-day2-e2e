# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [0.5.0] - 2026-11-23

### Fixed

- ETA could show **0 h**: linear regression predicted negative hours for short S1 tickets with experienced engineers (e.g. S1 Firewalls, 15 years → −6.3 h, clipped to 0; 14 of 971 test tickets negative)

### Changed

- Served model is now a **Gamma GLM** (`TweedieRegressor(power=2, link="log", alpha=0)`, same preprocessing): MAE 18.3 h (linear 18.5), RMSE 24.9 h (25.0), R² 0.20, S1 MAE 1.8 h (5.5), no negative predictions; the example S1 ticket now gets 2.3 h
- `model.py`: `build_preprocessor()`, `build_linear_pipeline()` (reference), `severity_floors()`, `input_ranges()`; metadata adds `model_type`, `metrics.linear_regression`, `min_hours_by_severity` (1st percentile of training hours: S1 0.9, S2 6.9, S3 8.3, S4 11.6 h) and `input_ranges`
- `scripts/train_model.py`: summary shows baseline, linear reference and GLM metrics plus the minimum ETAs
- `predictor.py`: numeric inputs clamped to the training range (`clamp_inputs`), result never below the severity minimum (`clip_and_round(hours, minimum)`); `predict()` returns `Prediction(hours, adjusted_inputs)`; models trained before 0.5.0 still load (no floor, no clamping)
- API: `PredictionOut.adjusted_inputs` (`[{field, original, used}]`, empty by default; additive, non-breaking); a warning is logged per clamped input with the `request_id`; OpenAPI descriptions updated
- Web UI: "Adjusted to the range seen in training" note under the ETA (`js/adjustments.js`); footer mentions the GLM
- Version 0.5.0 (`pyproject.toml`, image tags `netcore-tac-eta-api:0.5.0`, `netcore-tac-eta-web:0.5.0`); model retrained

### Added

- Notebook section 17 "Keeping ETAs Positive" (`[C50]`–`[C53]`): negative predictions, Gamma GLM, scorecard, safety nets; matching lecture notes
- Tests: GLM pipeline, positive predictions for extreme inputs, floors and ranges in metadata, clamping and floor in the predictor, `adjusted_inputs` in schema and route (+ log), `tests/web/adjustments.test.mjs`
- `docs/04-positive-eta.md` (prompt and Q&A log); README, TROUBLESHOOTING, CONTRIBUTING and SECURITY (supported 0.5.x) updated

## [0.4.0] - 2026-11-23

### Added

- **Web UI** (`web/`): plain HTML/CSS/JS (ES modules; no framework, build step or CDN) served by NGINX
  - **Home** (`/`): `README.md` rendered at runtime with vendored `marked` 18.1.3 (raw HTML escaped, repo links shown as text, heading anchors)
  - **Register Ticket** (`/register.html`): form mirroring `TicketIn`, 5 sample chips, client-side checks, ETA card (hours, days + hours, comparison with the fixed severity ETA, `model_version`, `request_id`), inline 422 errors + summary, 429 countdown from `Retry-After`, 503 / 502 / timeout / network messages, "Registered this session" list (`sessionStorage`, max 20)
  - **NetCore Light / Dark** themes with a header toggle (Light by default, saved in `localStorage`, applied before first paint)
  - Pure, unit-tested modules: `config`, `payload`, `chips`, `eta`, `api`, `history`, `theme`, `markdown`; thin page scripts `layout`, `home`, `register`, `theme-init`
- **NGINX** (`web/nginx/`): `nginxinc/nginx-unprivileged:1.30.6-alpine` (UID 101, port 8080); same-origin proxy for `/api/`, `/docs`, `/openapi.json` with a dynamic upstream (Docker DNS); `X-Forwarded-For` overwritten with the client IP; 502 problem+json when the API is down; strict CSP (relaxed only for `/docs`) and security headers; `/healthz`; gzip; 16 KB body limit
- `web/Dockerfile` (+ `web/Dockerfile.dockerignore` allow-list) with `nginx -t` at build time and a `HEALTHCHECK`; image 90 MB on disk / 26 MB compressed
- `docker-compose.yml` service `web` (`${WEB_PORT:-80}:8080`, waits for a healthy `eta-api`, read-only, tmpfs `/tmp`, `no-new-privileges`, 128 MB)
- JavaScript unit tests `tests/web/*.test.mjs` (70 tests, `node --test`, no npm packages)
- `Makefile`: `help` (default), `build`, `build-api`, `build-web`, `start` (`docker compose up -d --wait`), `stop`, `status`, `logs`, `predict` (through NGINX), `train`, `test`, `test-web`, `lock`; shell-neutral recipes (cmd, PowerShell, Git Bash); `build`/`start` train the model first if it is missing
- `data/sample_prediction_request.json` (sample S2 ticket for `make predict`) and `tests/test_sample_request.py`
- `docs/prompts/002-web-ui-prompt.md` (web UI build prompt), `docs/design/theme-options.html` (interactive theme preview with live WCAG contrast checks, now including NetCore Dark), `docs/03-web-ui.md` (prompt and Q&A log)
- `.env.example`: `WEB_PORT=80`

### Changed

- `pyproject.toml` version 0.4.0; image tags `netcore-tac-eta-api:0.4.0`, `netcore-tac-eta-web:0.4.0`
- `eta-api` is no longer published to the host (`expose: 8000`) and runs with `TRUST_PROXY_HEADERS=true` behind NGINX
- Healthcheck `start_interval` / `--start-interval=2s` (Compose and Dockerfiles): containers report healthy in seconds instead of ~30 s
- `.dockerignore` (API image): excludes `web/` and `Makefile`
- README (Web UI section, Compose/Makefile/configuration/examples, structure, image sizes), SECURITY (web UI and reverse proxy, CORS note, supported version 0.4.x), TROUBLESHOOTING (port 80, 502, internal API port, README/theme/CSP/node issues, Windows `pytest-current` error), CONTRIBUTING (web UI workflow, page-script test exception, upgrading `marked`), AGENTS + Copilot summary (`web/` folder), `docs/02-model-rest-api.md` (Makefile Q&A)

## [0.3.0] - 2026-11-23

### Added

- REST API (`src/netcore_tac/api/`): FastAPI + uvicorn service for the notebook's linear-regression ETA model
  - `POST /api/v1/predictions`, `GET /health` (liveness), `GET /ready` (readiness), Swagger UI `/docs`, `/openapi.json`
  - `settings.py` (pydantic-settings, `.env`, fail-fast `ConfigurationError`), `main.py` (`create_app` factory, lifespan model loading), `schemas.py` (Pydantic v2, `extra="forbid"`, OpenAPI examples), `predictor.py`, `routes.py`, `problems.py` (RFC 9457 problem details), `rate_limit.py` (100 req / 60 s per IP, 30 s block, `RateLimit-*` + `Retry-After`, probes exempt), `request_id.py` (`X-Request-ID`)
  - App stays up without a model file: `/health` 200, `/ready` and predictions 503
- Shared ML modules: `cleaning.py` (`clean_tickets`), `features.py` (feature lists, `add_tac_features`), `model.py` (`build_pipeline`, `train_model`, `save_model`, `load_model`, metadata)
- `scripts/train_model.py`: clean → 80/20 split → fit → evaluate → `models/eta_model.joblib` + `models/eta_model.json` (baseline MAE 20.5 h; model MAE 18.5 h, RMSE 25.0 h, R² 0.20 — matches the notebook)
- `models/` folder (`.gitkeep`; artefacts git-ignored) and its row in the `AGENTS.md` folder table
- `.env.example`, `requirements.lock` (pinned runtime dependencies), `Dockerfile` (multi-stage `python:3.12-slim`, non-root UID 10001, model presence check, `HEALTHCHECK`, library `tests/` folders removed; 566 MB on disk / 133 MB compressed vs 1.62 GB / 430 MB for `python:3.12`), `.dockerignore`, `docker-compose.yml` (`eta-api`: read-only, tmpfs `/tmp`, `no-new-privileges`, 512 MB)
- Unit tests: `test_cleaning`, `test_features`, `test_model`, `test_train_model_script`, `test_schemas`, `test_predictor`, `test_problems`, `test_rate_limit`, `test_request_id`, `test_settings`, `test_routes`, `test_main` (+ `conftest.py`)
- `docs/02-model-rest-api.md` — prompt and Q&A log for the REST API; `docs/prompts/001-model-rest-api-prompt.md`
- README API section, TROUBLESHOOTING rows, SECURITY API section (no auth, CORS disabled, per-process rate limiting, container hardening), CONTRIBUTING common tasks
- `docs/01-initial-setup-data-generation.md` — prompts and Q&A log for setup and data generation
- `notebooks/` folder (with `.gitkeep`) and its row in the `AGENTS.md` folder table
- `ipykernel` dev dependency for running notebooks in VS Code
- `notebooks/archive/ticket-resolution-ml-workflow-full.ipynb`: backup of the full detailed notebook (instructor reference)
- `.temp/notebook-lecture-notes.md`: instructor lecture notes, one entry per notebook cell tag (git-ignored)
- `notebooks/01-ticket-resolution-ml-workflow.ipynb`: title, business summary, learning objectives, setup, Part 0 (sections 1.1–1.9, including the first scikit-learn demo)
- Notebook Part 1 – Data Quality (sections 2.1–2.5): profiling, business metrics, label fixes, negative values, duplicates, mean vs median, IQR and outlier removal → `clean_df`
- Notebook Part 2 – Exploratory Data Analysis (sections 2.6–2.8): distribution and skew, severity/product/region/devices comparisons, correlation with leakage flagged, correlation vs cause, pivot tables, three insights
- Notebook Part 3 – Feature Engineering: feature lists and 80/20 split, one-hot encoding with an unseen product, scaling, `is_weekend` and `old_software` flags, leak-free preprocessing pipeline
- Notebook Part 4 – Linear Regression (sections 3.4, 3.5, 3.8): baseline, devices-only regression, full pipeline regression with driver ranking, MAE/RMSE/R² comparison, summary for support leadership

### Changed

- `pyproject.toml`: version 0.3.0; dependencies `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `joblib`; `matplotlib` and `seaborn` moved to a `notebook` dependency group (`[tool.uv] default-groups = ["dev", "notebook"]`) so the Docker image ships no plotting libraries
- `.gitignore`: `models/*.joblib`, `models/*.json`
- Notebook renamed to `notebooks/ticket-resolution-ml-workflow.ipynb` and slimmed for learners from escalation engineering: 251 → 85 cells, 16 sections in one running sequence, short notes only, one glossary, minimal EDA (1 section); simpler code (`duplicated()` for duplicates, flags added before the split, no `FunctionTransformer`); results unchanged (MAE 20.5 → 18.5 h)
- Every markdown cell tagged `[Cnn]`; code cells repeat the tag in their first comment
- `.gitignore`: `.temp/` (instructor-only files)
- Notebook review: ticket counts in the business summary and the 1.1/1.3 callouts now match the 5,000-ticket export; column-role table reduced to one line per role; y-axis labels added to both box plots; 3.3 pipeline cell split into two shorter cells

### Removed

- `notebooks/.gitkeep` (folder no longer empty)

## [0.2.0] - 2026-11-20

### Added

- `netcore_tac` package (`src/`): `config`, `generator`, `quality_issues`, `dataset`
- `scripts/generate_tickets.py` — CLI with `--n`, `--seed`, `--output`
- Synthetic NetCore TAC tickets with outliers, negative values, missing values, inconsistent labels and near duplicates
- Unit tests: `test_generator.py`, `test_quality_issues.py`, `test_dataset.py`

### Changed

- `pyproject.toml` — `uv_build` build backend so `netcore_tac` is importable
- Removed `.gitkeep` from `src/`, `scripts/`, `tests/` (no longer empty)

## [0.1.0] - 2026-11-20

### Added

- `AGENTS.md` — shared AI assistant rules
- `CLAUDE.md` and `.github/copilot-instructions.md` — pointers to `AGENTS.md`
- Standard files: `.gitignore`, `README.md`, `TROUBLESHOOTING.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `LICENSE` (MIT)
- Folder scaffold with `.gitkeep`: `src/`, `scripts/`, `tests/`, `data/`
- `pytest` as a dev dependency
