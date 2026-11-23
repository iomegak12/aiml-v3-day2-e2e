# Day 2 — TAC Desk Resolution-Time Prediction

ML training demonstration for **NetCore TAC Desk** (fictional networking vendor): predict ticket resolution hours at triage time.

- Business use case: [docs/business-use-case.txt](docs/business-use-case.txt)
- Session logs (prompts + Q&A): [docs/01-initial-setup-data-generation.md](docs/01-initial-setup-data-generation.md), [docs/02-model-rest-api.md](docs/02-model-rest-api.md)
- Lecture notes: `.temp/notebook-lecture-notes.md` (instructor-only, git-ignored); each entry matches a `[Cnn]` tag in the notebook
- Topics: Data Quality, EDA, Feature Engineering, Pipelines, Regression, Model Serving (REST API)

## Project Structure

```
day2/
├── .github/
│   └── copilot-instructions.md   # Copilot pointer → AGENTS.md
├── data/                         # Sample / synthetic data (+ sample_prediction_request.json)
├── docs/                         # Project & ML documentation (+ prompts/)
├── models/                       # Trained model artefacts (git-ignored, rebuilt by train_model.py)
├── notebooks/
│   ├── ticket-resolution-ml-workflow.ipynb      # Day 2 ML workflow (slim student version)
│   └── archive/
│       └── ticket-resolution-ml-workflow-full.ipynb   # Full detailed version (instructor reference)
├── scripts/
│   ├── generate_tickets.py       # CLI: build synthetic dataset → CSV
│   └── train_model.py            # CLI: clean → train → evaluate → save model + metadata
├── src/
│   └── netcore_tac/
│       ├── config.py             # Generator constants: probabilities, SLA hours, templates
│       ├── generator.py          # Clean ticket generation
│       ├── quality_issues.py     # Outliers, missing, variants, near duplicates
│       ├── dataset.py            # build_dataset(n, seed) pipeline
│       ├── cleaning.py           # clean_tickets(df): notebook Part 1 rules
│       ├── features.py           # Feature lists + add_tac_features(df)
│       ├── model.py              # build_pipeline / train_model / save_model / load_model
│       └── api/
│           ├── settings.py       # Settings from .env (pydantic-settings)
│           ├── main.py           # create_app() factory + module-level app
│           ├── schemas.py        # Request / response models + OpenAPI examples
│           ├── predictor.py      # Ticket → one-row DataFrame → prediction
│           ├── routes.py         # /api/v1/predictions, /health, /ready
│           ├── problems.py       # RFC 9457 problem details + exception handlers
│           ├── rate_limit.py     # Per-IP rate limiter + middleware
│           └── request_id.py     # X-Request-ID middleware
├── tests/                        # pytest unit tests
├── .env.example                  # Configuration template (copy to .env)
├── Dockerfile                    # Multi-stage slim image, non-root
├── docker-compose.yml            # eta-api service
├── Makefile                      # build / start / stop / predict shortcuts
├── requirements.lock             # Pinned runtime dependencies for Docker
├── AGENTS.md                     # AI assistant rules (single source of truth)
├── CLAUDE.md                     # Claude Code pointer → AGENTS.md
├── pyproject.toml
└── README.md
```

## Setup

```bash
uv sync          # runtime + dev + notebook groups (matplotlib/seaborn live in "notebook")
```

## Generate the Dataset

```bash
uv run python scripts/generate_tickets.py                     # defaults below
uv run python scripts/generate_tickets.py --n 5000 --seed 42 --output data/netcore_tickets.csv
```

| Option | Default |
|--------|---------|
| `--n` | 2000 (near duplicates included) |
| `--seed` | 42 (same seed → identical output) |
| `--output` | `data/netcore_tickets.csv` |

- The committed `data/netcore_tickets.csv` has 5,000 tickets (`--n 5000 --seed 42`).

### Columns

`ticket_id`, `created_at`, `product_family`, `severity`, `customer_tier`, `region`, `channel`, `devices_affected`, `software_version_months`, `prior_tickets_90d`, `engineer_experience_years`, `first_response_minutes`, `customer_comments`, `escalation_count`, `reopened`, `resolution_code`, `sla_breached`, `resolution_hours` (target)

### Injected Data-Quality Issues

| Issue | Detail |
|-------|--------|
| Outliers | ~1% → 1500–3000 h, Hardware RMA |
| Negative values | 10 random `first_response_minutes` |
| Missing | ~5% `engineer_experience_years`, ~5% `first_response_minutes`, 1% `severity` |
| Inconsistent severity | ~3% → `SEV2`, `Sev 2`, `Sev-2`, `s2` |
| Inconsistent region | ~3% → `emea`, `amer `, ` APJC `, … |
| Near duplicates | ~2% Email/Phone rows copied: new ID, +1–15 min, channel swapped |

- `sla_breached` is computed from the clean severity, after outliers.

## Train the Model

```bash
uv run python scripts/train_model.py            # --data data/netcore_tickets.csv --output-dir models/
```

- Same code as the notebook: `clean_tickets` → `add_tac_features` → 80/20 split (`random_state=42`) → fit on the training split → evaluate on the test split
- Writes `models/eta_model.joblib` (pipeline) and `models/eta_model.json` (version, `trained_at`, scikit-learn version, row counts, features, test metrics)
- Expected: 4,851 clean tickets; train 3,880 / test 971; baseline MAE 20.5 h; model MAE 18.5 h, RMSE 25.0 h, R² 0.20

## REST API

### Architecture

- **FastAPI + uvicorn**; `create_app(settings)` factory; the lifespan loads the model **once** at startup
- **Same code for training and serving**: `predictor.py` reuses `features.add_tac_features` and the saved scikit-learn pipeline (no copied logic)
- **Errors**: RFC 9457 `application/problem+json` for 404, 405, 422, 429, 500 and 503, with `request_id`
- **Rate limit**: 100 requests / 60 s per client IP, then a 30 s block (429 + `Retry-After`); `/health` and `/ready` exempt
- **No authentication, no CORS** (see [SECURITY.md](SECURITY.md)); configuration from `.env`

### Run Locally

```bash
uv run python scripts/train_model.py                 # 1. train (once)
cp .env.example .env                                  # 2. optional: customise settings
uv run uvicorn netcore_tac.api.main:app --no-proxy-headers   # 3. serve on http://127.0.0.1:8000
```

- Swagger UI: <http://127.0.0.1:8000/docs> · OpenAPI: <http://127.0.0.1:8000/openapi.json>
- `--no-proxy-headers`: let the app (not uvicorn) decide whether to trust `X-Forwarded-For`
- Run from `day2/`: `MODEL_PATH` and `.env` are resolved from the working directory

### Docker / Compose

```bash
uv run python scripts/train_model.py     # the model is baked into the image
docker compose up --build -d             # service eta-api on http://127.0.0.1:${PORT:-8000}
docker compose ps                        # STATUS shows (healthy)
docker compose down
```

- Image: multi-stage `python:3.12-slim`, non-root user (UID 10001), single uvicorn worker, built-in `HEALTHCHECK`
- Compose: `read_only` filesystem + `/tmp` tmpfs, `no-new-privileges`, 512 MB memory limit, `restart: unless-stopped`
- Image size (0.3.0): **566 MB** on disk / 133 MB compressed, vs 1.62 GB / 430 MB for full `python:3.12` (library test suites are removed at build time)

### Makefile Shortcuts

```bash
make            # list targets (help)
make build      # trains the model first if models/eta_model.joblib is missing, then builds the image
make start      # docker compose up -d --wait (returns once the container is healthy)
make predict    # POST data/sample_prediction_request.json to /api/v1/predictions
make stop       # docker compose down
```

- Also: `make status`, `make logs`, `make train`, `make test`, `make lock`
- Another port: `make predict PORT=8080` (or set `PORT` in `.env`, which the Makefile reads)
- Requires GNU Make (Windows: `choco install make`) and curl; works from PowerShell, cmd and Git Bash

### Endpoints

| Method | Path | Purpose | Rate limited |
|--------|------|---------|--------------|
| POST | `/api/v1/predictions` | Predict resolution hours for one ticket | Yes |
| GET | `/health` | Liveness: 200 while the process runs | No |
| GET | `/ready` | Readiness: 200 when the model is loaded, else 503 | No |
| GET | `/docs` | Swagger UI | Yes |
| GET | `/openapi.json` | OpenAPI schema | Yes |

### Examples

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"created_at": "2026-11-23T10:15:00", "product_family": "Routers", "severity": "S2",
       "customer_tier": "Gold", "region": "EMEA", "channel": "Phone", "devices_affected": 4,
       "software_version_months": 40, "prior_tickets_90d": 1,
       "engineer_experience_years": 6.5, "first_response_minutes": 20.0}'
# {"predicted_hours":32.0,"model_version":"0.3.0","request_id":"…"}

curl -s http://127.0.0.1:8000/health     # {"status":"ok"}
curl -s http://127.0.0.1:8000/ready      # {"status":"ready","model_version":"0.3.0","trained_at":"…"}
```

- Request fields: `created_at` (ISO-8601), `product_family` (1–50 chars, unseen allowed), `severity` S1–S4, `customer_tier` Platinum/Gold/Silver, `region` AMER/EMEA/APJC, `channel` Email/Phone/Portal, `devices_affected` 1–1000, `software_version_months` 0–240, `prior_tickets_90d` 0–100, `engineer_experience_years` 0–50 or null, `first_response_minutes` 0–10080 or null
- Unknown fields → 422

### Configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `APP_NAME` | NetCore TAC ETA API | Title shown in OpenAPI |
| `APP_ENV` | development | development / production |
| `HOST` | 0.0.0.0 | Bind address |
| `PORT` | 8000 | Bind port (Compose: published host port) |
| `LOG_LEVEL` | info | uvicorn / app log level |
| `MODEL_PATH` | models/eta_model.joblib | Trained pipeline |
| `MODEL_METADATA_PATH` | models/eta_model.json | Model metadata |
| `RATE_LIMIT_REQUESTS` | 100 | Requests allowed per window |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | Window length |
| `RATE_LIMIT_BLOCK_SECONDS` | 30 | Block after the limit is exceeded |
| `TRUST_PROXY_HEADERS` | false | Use X-Forwarded-For for the client IP |
| `DOCS_ENABLED` | true | Serve /docs, /redoc and /openapi.json |

- Invalid values stop startup with a message naming the variable
- Rate-limit counters are **per process**: with several workers or replicas each counts separately

### Refresh the Docker Lock File

```bash
uv export --frozen --no-default-groups --no-emit-project -o requirements.lock
```

- Run after any `uv add` / `uv remove` / `uv lock --upgrade`; commit `requirements.lock`

## Run Tests

```bash
uv run pytest
```

- Unit tests only (no server, no TestClient, no Docker)

## AI Assistant Rules

- Claude Code and GitHub Copilot both follow [AGENTS.md](AGENTS.md).

## Project Documents

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CHANGELOG.md](CHANGELOG.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [LICENSE](LICENSE) — MIT
