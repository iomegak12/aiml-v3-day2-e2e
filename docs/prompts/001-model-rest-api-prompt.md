1. Role and Context
You are a senior Python and MLOps engineer working in the day2/ project of an ML training course. Follow AGENTS.md exactly: modular code in src/, reusable scripts in scripts/, data in data/, docs in docs/, mandatory pytest unit tests in tests/, and README/CHANGELOG updated with every change. If something is genuinely blocking, ask me multiple-choice questions before proceeding; otherwise apply the decisions in this prompt without asking again.

What already exists

Python ≥ 3.12, managed with uv. day2 is a member of a uv workspace whose root (and uv.lock) is the parent folder demonstrations/.
pyproject.toml: package netcore_tac (build backend uv_build, source in src/netcore_tac/); dependencies numpy, pandas, scikit-learn, matplotlib, seaborn; dev group pytest, ipykernel.
src/netcore_tac/: synthetic-data generator (config.py, generator.py, quality_issues.py, dataset.py). config.py holds generator constants; do not reuse that name for API settings.
data/netcore_tickets.csv: 5,000 synthetic TAC tickets (generated with scripts/generate_tickets.py --n 5000 --seed 42).
notebooks/ticket-resolution-ml-workflow.ipynb: the reference ML workflow. Its logic must be reproduced exactly (section 3).
Business purpose: at triage, predict how many hours a ticket will take to resolve, replacing the fixed per-severity ETA (S1 4 h, S2 24 h, S3 48 h, S4 72 h).

2. Goal and Non-Goals
Build: a FastAPI + uvicorn REST API that serves the notebook's trained linear-regression model, with OpenAPI docs, Swagger UI, rate limiting, RFC 9457 errors, health and readiness probes, .env configuration, a slim Docker image and Docker Compose.

Out of scope (do not build): authentication, CORS, a database, batch prediction, a retraining endpoint, integration or end-to-end tests, a front end.

3. Move the ML Logic into Modules and Train from a Script
Create small, single-purpose modules so the training script and the API use the same code (no copies, no drift between training and serving):

Module	Responsibility
src/netcore_tac/cleaning.py	clean_tickets(df) -> DataFrame, reproducing the notebook's Part 1 exactly (below)
src/netcore_tac/features.py	Feature lists (NUMERIC_FEATURES, FLAG_FEATURES, CATEGORICAL_FEATURES, TARGET) and add_tac_features(df)
src/netcore_tac/model.py	build_pipeline(), train_model(df), save_model(...), load_model(...), model metadata
Cleaning rules (notebook Part 1). Never modify the input; work on a copy.

Severity: upper-case, remove "EV", spaces and "-" (so "Sev-1", "SEV1", "s1" → "S1"); blanks stay blank.
Region: strip whitespace and upper-case.
first_response_minutes < 0 → NaN.
Duplicates: sort by created_at; drop rows that duplicate an earlier row on every column except ticket_id, channel, created_at (keep="first").
Remove tickets with resolution_hours > 1000 (parked Hardware RMA cases).
Features.

Numeric: devices_affected, software_version_months, prior_tickets_90d, engineer_experience_years, first_response_minutes.
Flags: is_weekend (created_at weekday ≥ 5) and old_software (software_version_months > 36), as 0/1 ints; add_tac_features then drops created_at.
Categorical: product_family, severity, customer_tier, region, channel.
Never inputs (leakage or not known at triage): resolution_code, escalation_count, reopened, sla_breached, ticket_id, customer_comments.
Pipeline. Pipeline([("prep", ColumnTransformer([...], verbose_feature_names_out=False)), ("model", LinearRegression())]):

numeric → SimpleImputer(strategy="median") → StandardScaler()
flags → "passthrough"
categorical → SimpleImputer(strategy="most_frequent") → OneHotEncoder(handle_unknown="ignore", sparse_output=False)
Training script scripts/train_model.py (thin; argparse: --data default data/netcore_tickets.csv, --output-dir default models/):

Load CSV (created_at as datetime) → clean_tickets → add_tac_features → 80/20 train_test_split(random_state=42) → fit on the training split → evaluate on the test split. Save that training-split model (no refit on all data), exactly as in the notebook.
Save models/eta_model.joblib (with joblib) and models/eta_model.json metadata: model_version (from pyproject.toml version), trained_at (UTC ISO-8601), scikit_learn_version, row counts, feature lists, and test metrics for baseline (DummyRegressor(strategy="mean")) and model: MAE, RMSE (np.sqrt(mean_squared_error(...))), R².
Expected results (must match the notebook): 4,851 clean tickets; 3,880 train / 971 test; baseline MAE ≈ 20.5 h; model MAE ≈ 18.5 h, RMSE ≈ 25.0 h, R² ≈ 0.20. Print them in one short summary.
models/: add to the AGENTS.md folder table ("Trained model artefacts"); git-ignore models/*.joblib and models/*.json, and keep models/.gitkeep.

4. API Package
Create src/netcore_tac/api/ with one responsibility per module:

Module	Responsibility
settings.py	Settings (pydantic-settings) loaded from .env
main.py	create_app(settings) -> FastAPI factory + module-level app; lifespan loads the model once at startup
schemas.py	Pydantic v2 request/response models with OpenAPI examples
predictor.py	Wraps the loaded pipeline: request → one-row DataFrame → add_tac_features → predict
routes.py	/api/v1/predictions, /health, /ready
problems.py	RFC 9457 problem builders and exception handlers
rate_limit.py	Rate-limiter logic and middleware
Endpoints

Method	Path	Purpose
POST	/api/v1/predictions	Predict resolution hours for one ticket
GET	/health	Liveness: process is up (always 200 while running)
GET	/ready	Readiness: 200 when the model is loaded, else 503 problem+json
GET	/docs	Swagger UI
GET	/openapi.json	OpenAPI schema
Request body (TicketIn)

created_at: datetime (ISO-8601)
product_family: free string, 1–50 chars (unseen products are allowed; the encoder ignores them)
severity: enum S1–S4; customer_tier: enum Platinum, Gold, Silver; region: enum AMER, EMEA, APJC; channel: enum Email, Phone, Portal
devices_affected: int ≥ 1, ≤ 1000; software_version_months: int 0–240; prior_tickets_90d: int 0–100
engineer_experience_years: float 0–50 or null; first_response_minutes: float 0–10080 or null (nulls are filled by the pipeline)
Reject unknown fields (extra="forbid").
Response (PredictionOut): predicted_hours (float, rounded to 1 dp, never below 0), model_version (str), request_id (UUID4 string, also returned in an X-Request-ID header).

5. OpenAPI and Swagger UI
App metadata: title "NetCore TAC ETA API", version from pyproject.toml, a short description of the model, its inputs, and its test MAE (from metadata).
Tags: predictions, operations. Every route has a summary, a description and a request example (one realistic S2 ticket).
Document error responses (422, 429, 503, 500) on each route with the problem-details schema and application/problem+json media type.
DOCS_ENABLED=false disables /docs, /redoc and /openapi.json.

6. Error Handling: RFC 9457 Problem Details
All errors use Content-Type: application/problem+json with members type (URI, e.g. https://netcore.example/problems/validation-error, or about:blank), title, status, detail, instance (the request path), plus extensions request_id and, for validation, errors (list of {field, message}).
Handlers: RequestValidationError → 422; HTTPException/Starlette 404 and 405; rate limit → 429 (+ Retry-After); model not loaded → 503; any unhandled exception → 500 with a generic detail. Never leak stack traces or internal paths; log them server-side with the request_id.

7. Rate Limiting
Per client IP, in memory: 100 requests per 60 seconds. The request that exceeds the limit starts a 30-second block; every request from that IP during the block gets 429 with Retry-After = remaining seconds (30 at the start).
Also send RateLimit-Limit, RateLimit-Remaining and RateLimit-Reset headers on normal responses.
Exempt /health and /ready (probes must never be throttled).
Client IP: request.client.host; use the first X-Forwarded-For address only when TRUST_PROXY_HEADERS=true.
Thread/async-safe (a lock), an injectable clock for unit tests, and stale entries cleaned up so memory doesn't grow without bound.
All limits come from settings. Document clearly (README + SECURITY) that counters are per process: with several workers or replicas, each counts separately.

8. Health and Readiness
GET /health → 200 {"status": "ok"} whenever the process is running; no model access.
GET /ready → 200 {"status": "ready", "model_version": ..., "trained_at": ...} once the model and metadata are loaded; otherwise 503 problem+json. If the model file is missing at startup, the app still starts (so /health works) but stays not-ready, and predictions return 503.

9. CORS: Disabled
Do not add CORSMiddleware; the API sends no Access-Control-* headers, so browsers block cross-origin calls. State this, and why, in SECURITY.md and the README.

10. Configuration: .env and .env.example
.env is git-ignored (already in .gitignore); commit .env.example with safe defaults and a comment per variable. Invalid values must fail fast at startup with a clear message.
Variable	Default	Meaning
APP_NAME	NetCore TAC ETA API	Title shown in OpenAPI
APP_ENV	development	development / production
HOST	0.0.0.0	Bind address
PORT	8000	Bind port
LOG_LEVEL	info	uvicorn / app log level
MODEL_PATH	models/eta_model.joblib	Trained pipeline
MODEL_METADATA_PATH	models/eta_model.json	Model metadata
RATE_LIMIT_REQUESTS	100	Requests allowed per window
RATE_LIMIT_WINDOW_SECONDS	60	Window length
RATE_LIMIT_BLOCK_SECONDS	30	Block after the limit is exceeded
TRUST_PROXY_HEADERS	false	Use X-Forwarded-For for the client IP
DOCS_ENABLED	true	Serve /docs and /openapi.json

11. Dependencies
Add with uv add: fastapi, uvicorn[standard], pydantic-settings, joblib. Use only these plus the existing numpy, pandas and scikit-learn at runtime.
Move matplotlib and seaborn into a notebook dependency group (keep them installed locally via [tool.uv] default-groups = ["dev", "notebook"]), so the Docker image doesn't ship plotting libraries.
The lock file lives at the workspace root. For Docker, export a pinned runtime lock inside day2/ (e.g. uv export --frozen --package day2 --no-default-groups --no-emit-project -o requirements.lock), commit it, and document how to refresh it.

12. Docker, Compose and .dockerignore
Dockerfile (build context day2/):

Multi-stage on python:3.12-slim. Builder: install uv, create /opt/venv, install from requirements.lock, then install the project without dependencies. Runtime: copy only /opt/venv, src/ and models/.
Non-root user (fixed UID, e.g. 10001), WORKDIR /app, PYTHONDONTWRITEBYTECODE=1, PYTHONUNBUFFERED=1, no build tools in the final stage, EXPOSE 8000.
HEALTHCHECK with a one-line Python urllib call to /health (no curl in slim images).
CMD runs uvicorn with netcore_tac.api.main:app, host and port from the environment, a single worker (the rate limiter is per process).
The model is baked into the image: the build must fail with a clear message if models/eta_model.joblib is missing ("run uv run python scripts/train_model.py first").
Target: final image clearly smaller than a full python:3.12 image; report the size.
.dockerignore: .git, .venv, __pycache__, *.pyc, .pytest_cache, .temp/, notebooks/, data/, docs/, tests/, .env, *.ipynb, IDE folders; keep src/, models/, pyproject.toml, requirements.lock, README.md, LICENSE.

docker-compose.yml: one service eta-api: build ., env_file: .env, port ${PORT:-8000}:8000, healthcheck mirroring the Dockerfile, restart: unless-stopped, read_only: true with a tmpfs for /tmp, security_opt: ["no-new-privileges:true"], memory limit (e.g. 512m).

13. Tests: Module Unit Tests Only
Use pytest; no FastAPI TestClient, no running server, no Docker, no integration tests. Cover:

cleaning: each rule above (labels, negatives, duplicates, >1,000 h), input not modified.
features: flags on known dates and software ages; created_at dropped.
model: train on a small dataset from netcore_tac.dataset.build_dataset(n=400, seed=1); save/load round-trip gives identical predictions; metadata fields present; no leakage column in the inputs.
predictor: unseen product and null experience still predict; output ≥ 0 and rounded.
schemas: valid example passes; bad enum, out-of-range number and extra field fail.
problems: builders produce the RFC 9457 fields and media type.
rate_limit: 100 allowed, 101st blocked, Retry-After counts down, unblocked after 30 s, window reset after 60 s, probes exempt (fake clock, no sleeping).
settings: defaults, .env overrides, invalid values rejected.
uv run pytest must pass with all existing tests.

14. Documentation Updates
README.md: an API section (architecture in a few bullets, train → run locally → Docker/Compose, endpoint table, curl examples for predict/health/ready, configuration table, Swagger link), updated project structure.
TROUBLESHOOTING.md: model file not found / /ready 503; port already in use; 429 and Retry-After; .env validation errors; Docker build fails without a model; refreshing requirements.lock.
SECURITY.md: no authentication (deploy behind a gateway), CORS disabled, rate limiting and its per-process limit, non-root read-only container, no secrets in images, .env never committed, error responses never expose internals.
CONTRIBUTING.md: how to train, run the API, run the tests and refresh the lock file.
CHANGELOG.md: version 0.3.0 entry; bump pyproject.toml to 0.3.0.
AGENTS.md: add the models/ folder row.

15. Acceptance Criteria
 uv run python scripts/train_model.py prints MAE ≈ 18.5 h vs baseline ≈ 20.5 h and writes the model + metadata.
 uv run uvicorn netcore_tac.api.main:app serves /docs; /openapi.json shows the tags, examples and problem responses.
 POST /api/v1/predictions with the documented example returns 200 with predicted_hours, model_version, request_id.
 Invalid input → 422 application/problem+json with an errors list.
 The 101st request within 60 s → 429 with Retry-After: 30; requests succeed again after 30 s; /health is never throttled.
 Without a model file: /health 200, /ready 503, predictions 503.
 No Access-Control-Allow-Origin header on any response.
 docker compose up --build → container healthy, runs as the non-root user, predictions work; image size reported.
 uv run pytest passes; all listed docs updated.