# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | Yes       |
| < 0.3   | No        |

## Reporting a Vulnerability

- Email: `<security-contact@example.com>`
- Do **not** open a public issue for security problems
- Include: description, steps to reproduce, impact
- Expect an acknowledgement within 5 business days

## Data Notice

- All data in `data/` is synthetic / sample data — no real customer information
- Never commit secrets, credentials or `.env` files

## REST API (NetCore TAC ETA API)

### No Authentication

- The API has **no authentication or authorisation** (out of scope for this course project)
- Deploy it only behind an API gateway / reverse proxy that handles authentication, TLS and access control
- Do not expose the container port directly to the internet

### CORS Disabled

- No `CORSMiddleware`; responses carry **no** `Access-Control-*` headers
- Browsers therefore block cross-origin JavaScript calls; server-to-server calls (curl, services) still work
- Why: there is no browser front end, and without authentication an open CORS policy would let any website call the API from a user's browser
- If a front end is ever added, allow only its exact origin, at the gateway or with an explicit allow-list

### Rate Limiting

- Per client IP, in memory: `RATE_LIMIT_REQUESTS` (100) per `RATE_LIMIT_WINDOW_SECONDS` (60); the request that exceeds it starts a `RATE_LIMIT_BLOCK_SECONDS` (30) block with `429` + `Retry-After`
- `/health` and `/ready` are exempt so probes are never throttled
- **Counters are per process**: with several uvicorn workers or container replicas each counts separately (effective limit = limit × processes). The image runs one worker; for a fleet-wide limit, rate-limit at the gateway or use a shared store (e.g. Redis)
- Counters reset when the process restarts
- `X-Forwarded-For` is used only when `TRUST_PROXY_HEADERS=true`; enable it **only** behind a trusted proxy, otherwise clients can spoof their IP and bypass the limit. Run uvicorn with `--no-proxy-headers` (the Docker image does) so the app alone makes this decision

### Container Hardening

- Non-root user (UID 10001); multi-stage build with no build tools in the final image
- Compose: `read_only: true` root filesystem with a `/tmp` tmpfs, `no-new-privileges:true`, 512 MB memory limit
- No secrets in the image: `.env` is excluded by `.dockerignore` and injected at runtime via `env_file`

### Configuration and Secrets

- `.env` is git-ignored and never committed; `.env.example` holds only safe defaults
- Invalid settings stop startup (fail fast) instead of running with unexpected values

### Error Responses

- All errors are RFC 9457 problem details with generic messages and a `request_id`
- Stack traces and internal paths are **never** returned to clients; they are logged server-side with the `request_id` for correlation

### Model Files

- `models/*.joblib` is a pickle: loading it can execute code. Load only models you trained yourself; never accept model files from untrusted sources
