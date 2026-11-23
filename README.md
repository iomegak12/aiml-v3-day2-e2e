# Day 2 — TAC Desk Resolution-Time Prediction

ML training demonstration for **NetCore TAC Desk** (fictional networking vendor): predict ticket resolution hours at triage time.

- Business use case: [docs/business-use-case.txt](docs/business-use-case.txt)
- Session logs (prompts + Q&A): [docs/01-initial-setup-data-generation.md](docs/01-initial-setup-data-generation.md), [docs/02-model-rest-api.md](docs/02-model-rest-api.md), [docs/03-web-ui.md](docs/03-web-ui.md), [docs/04-positive-eta.md](docs/04-positive-eta.md)
- Build prompts: [docs/prompts/](docs/prompts/) — `001` REST API, `002` web UI
- Web UI theme options (open in a browser): [docs/design/theme-options.html](docs/design/theme-options.html) — NetCore Light / Dark chosen
- Lecture notes: `.temp/notebook-lecture-notes.md` (instructor-only, git-ignored); each entry matches a `[Cnn]` tag in the notebook
- Topics: Data Quality, EDA, Feature Engineering, Pipelines, Regression, Model Serving (REST API), Web UI (NGINX)

## Project Structure

```
day2/
├── .github/
│   └── copilot-instructions.md   # Copilot pointer → AGENTS.md
├── data/                         # Sample / synthetic data (+ sample_prediction_request.json)
├── docs/                         # Project & ML documentation (+ prompts/, design/)
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
│   └── web/                      # node --test unit tests for web/site/js (*.test.mjs)
├── web/                          # Web UI image (NGINX + static site)
│   ├── Dockerfile                # nginx-unprivileged, non-root, port 8080
│   ├── Dockerfile.dockerignore   # build-context allow-list for the web image
│   ├── nginx/                    # default.conf, security-headers.conf, proxy.conf
│   └── site/
│       ├── index.html            # Home: README rendered as HTML
│       ├── register.html         # Register Ticket: form + sample chips → ETA
│       ├── css/                  # tokens.css (NetCore light/dark), base.css, components.css
│       ├── js/                   # config, payload, chips, eta, api, history, theme, markdown (+ page scripts)
│       └── vendor/               # marked 18.1.3 (ESM build) + licence
├── .env.example                  # Configuration template (copy to .env)
├── Dockerfile                    # API image: multi-stage slim, non-root
├── docker-compose.yml            # eta-api (internal) + web (NGINX, published)
├── Makefile                      # build / start / stop / predict / test-web shortcuts
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
- **Served model: Gamma GLM** (`TweedieRegressor(power=2, link="log", alpha=0)`, notebook section 17). Linear regression (notebook section 15) is still trained as a reference, but it predicts *negative* hours for short S1 tickets handled by senior engineers (14 of 971 test tickets); the GLM's effects multiply instead of add, so every ETA is positive
- Writes `models/eta_model.joblib` (pipeline) and `models/eta_model.json` (version, model type, `trained_at`, scikit-learn version, row counts, features, test metrics, `min_hours_by_severity`, `input_ranges`)
- Expected: 4,851 clean tickets; train 3,880 / test 971; baseline MAE 20.5 h; linear regression MAE 18.5 h; **GLM MAE 18.3 h, RMSE 24.9 h, R² 0.20**, S1 MAE 1.8 h (linear 5.5 h), 0 negative predictions
- Minimum ETA per severity (1st percentile of training hours): S1 0.9 h · S2 6.9 h · S3 8.3 h · S4 11.6 h

## REST API

### Architecture

- **FastAPI + uvicorn**; `create_app(settings)` factory; the lifespan loads the model **once** at startup
- **Same code for training and serving**: `predictor.py` reuses `features.add_tac_features` and the saved scikit-learn pipeline (no copied logic)
- **Always a realistic ETA**: Gamma GLM (never negative) + per-severity minimum ETA from the model metadata; numeric inputs outside the training range (e.g. experience > 20 years, devices > 54) are clamped to it, listed in the response as `adjusted_inputs` and logged with the `request_id`
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
uv run python scripts/train_model.py     # the model is baked into the API image
docker compose up --build -d --wait      # eta-api (internal) + web on http://localhost:${WEB_PORT:-80}
docker compose ps                        # both services show (healthy)
docker compose down
```

- In Compose the API is **not published**: browsers and curl reach it through NGINX (see [Web UI](#web-ui)); `eta-api` runs with `TRUST_PROXY_HEADERS=true`
- API image: multi-stage `python:3.12-slim`, non-root user (UID 10001), single uvicorn worker, built-in `HEALTHCHECK`
- Compose: `read_only` filesystem + `/tmp` tmpfs, `no-new-privileges`, memory limits (API 512 MB, web 128 MB), `restart: unless-stopped`
- Image sizes (0.4.0): API **566 MB** on disk / 133 MB compressed (vs 1.62 GB / 430 MB for full `python:3.12`; library test suites removed at build time); web **90 MB** / 26 MB

### Makefile Shortcuts

```bash
make            # list targets (help)
make build      # both images; trains the model first if models/eta_model.joblib is missing
make start      # docker compose up -d --wait (returns once API and web are healthy)
make predict    # POST data/sample_prediction_request.json through NGINX
make stop       # docker compose down
```

- Also: `make build-api`, `make build-web`, `make status`, `make logs`, `make train`, `make test`, `make test-web`, `make lock`
- Another port: `make start predict WEB_PORT=8080` (or set `WEB_PORT` in `.env`, which the Makefile reads)
- Requires GNU Make (Windows: `choco install make`), curl and Node ≥ 22 (for `test-web`); works from PowerShell, cmd and Git Bash

### Endpoints

| Method | Path | Purpose | Rate limited |
|--------|------|---------|--------------|
| POST | `/api/v1/predictions` | Predict resolution hours for one ticket | Yes |
| GET | `/health` | Liveness: 200 while the process runs | No |
| GET | `/ready` | Readiness: 200 when the model is loaded, else 503 | No |
| GET | `/docs` | Swagger UI | Yes |
| GET | `/openapi.json` | OpenAPI schema | Yes |

### Examples

Local uvicorn (port 8000). With Docker Compose use `http://localhost/api/v1/predictions` instead; `/health` and `/ready` stay internal.

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"created_at": "2026-11-23T10:15:00", "product_family": "Routers", "severity": "S2",
       "customer_tier": "Gold", "region": "EMEA", "channel": "Phone", "devices_affected": 4,
       "software_version_months": 40, "prior_tickets_90d": 1,
       "engineer_experience_years": 6.5, "first_response_minutes": 20.0}'
# {"predicted_hours":31.0,"model_version":"0.5.0","request_id":"…","adjusted_inputs":[]}
# out-of-range input, e.g. "engineer_experience_years": 35 →
#   "adjusted_inputs":[{"field":"engineer_experience_years","original":35.0,"used":20.0}]

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
| `PORT` | 8000 | Bind port for local uvicorn (Compose: fixed 8000, internal) |
| `WEB_PORT` | 80 | Compose / Makefile: host port of the web UI (use 8080 if 80 is taken) |
| `LOG_LEVEL` | info | uvicorn / app log level |
| `MODEL_PATH` | models/eta_model.joblib | Trained pipeline |
| `MODEL_METADATA_PATH` | models/eta_model.json | Model metadata |
| `RATE_LIMIT_REQUESTS` | 100 | Requests allowed per window |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | Window length |
| `RATE_LIMIT_BLOCK_SECONDS` | 30 | Block after the limit is exceeded |
| `TRUST_PROXY_HEADERS` | false | Use X-Forwarded-For for the client IP (Compose sets `true` for eta-api behind NGINX) |
| `DOCS_ENABLED` | true | Serve /docs, /redoc and /openapi.json |

- Invalid values stop startup with a message naming the variable
- Rate-limit counters are **per process**: with several workers or replicas each counts separately

### Refresh the Docker Lock File

```bash
uv export --frozen --no-default-groups --no-emit-project -o requirements.lock
```

- Run after any `uv add` / `uv remove` / `uv lock --upgrade`; commit `requirements.lock`

## Web UI

Plain HTML, CSS and JavaScript (ES modules; no framework, build step or CDN) served by NGINX, which also proxies the API on the same origin, so CORS stays disabled.

```
Browser ──► web (NGINX, host :${WEB_PORT:-80} → container 8080)
              ├── /  /register.html  /css  /js  /vendor  /README.md      static site
              └── /api/…  /docs  /openapi.json  ──►  eta-api:8000 (internal only)
```

| Page | What it does |
|------|--------------|
| **Home** (`/`) | Fetches `/README.md` and renders it with the vendored `marked` (raw HTML escaped; repo links shown as text) |
| **Register Ticket** (`/register.html`) | Form mirroring `TicketIn` + 5 sample chips → **Get ETA** → predicted hours vs the fixed severity ETA, `model_version`, `request_id`, a note when inputs were adjusted to the training range; "Registered this session" list (`sessionStorage`, max 20) |

- **Run:** `make start`, then open <http://localhost> (or `http://localhost:<WEB_PORT>`); Swagger UI at <http://localhost/docs>
- **Theme:** NetCore **Light** (default) / **Dark** toggle in the header, remembered in `localStorage`; palettes in [docs/design/theme-options.html](docs/design/theme-options.html)
- **Errors:** client checks before calling the API; 422 → inline field errors + summary; 429 → countdown banner from `Retry-After`; 503 → model not ready; 502 → API unavailable (problem+json from NGINX)
- **Security:** strict Content-Security-Policy (no inline script/style), `nosniff`, `DENY` framing, `no-referrer`; NGINX overwrites `X-Forwarded-For` so rate limiting stays per real client (see [SECURITY.md](SECURITY.md))
- **Vendored:** `marked` 18.1.3 ESM build in `web/site/vendor/` (MIT); only its source-map comment is removed

## Run Tests

```bash
uv run pytest        # Python unit tests
make test-web        # JavaScript unit tests: node --test "tests/web/*.test.mjs" (Node ≥ 22, no npm packages)
```

- Unit tests only (no server, no TestClient, no browser, no Docker)
- Page scripts (`layout.js`, `home.js`, `register.js`, `theme-init.js`) are thin DOM glue without unit tests (that would need jsdom); all their logic lives in the tested modules

## AI Assistant Rules

- Claude Code and GitHub Copilot both follow [AGENTS.md](AGENTS.md).

## Project Documents

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CHANGELOG.md](CHANGELOG.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [LICENSE](LICENSE) — MIT
