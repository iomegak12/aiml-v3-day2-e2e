# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added

- `Makefile`: `help` (default), `build` (trains the model first if missing), `start` (`docker compose up -d --wait`), `stop`, `predict` (curl with the sample payload), `status`, `logs`, `train`, `test`, `lock`; shell-neutral recipes (cmd, PowerShell, Git Bash)
- `data/sample_prediction_request.json`: sample S2 ticket for `make predict`
- `tests/test_sample_request.py`: sample payload is a valid `TicketIn` and matches the OpenAPI example

### Changed

- Healthcheck `start_interval` / `--start-interval=2s` (Compose and Dockerfile): container reports healthy in ~3 s instead of ~30 s
- `.dockerignore`: `Makefile`
- README (Makefile section, structure), CONTRIBUTING, TROUBLESHOOTING (make / curl issues), `docs/02-model-rest-api.md` (Makefile Q&A)

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
