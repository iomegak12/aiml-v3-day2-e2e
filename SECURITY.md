# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.5.x   | Yes       |
| < 0.5   | No        |

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
- Do not expose the container port directly to the internet (Compose publishes only the NGINX web port; the web UI has no authentication either)

### CORS Disabled

- No `CORSMiddleware`; responses carry **no** `Access-Control-*` headers
- Browsers therefore block cross-origin JavaScript calls; server-to-server calls (curl, services) still work
- Why: without authentication, an open CORS policy would let any website call the API from a user's browser
- The web UI (0.4.0) does not need CORS: NGINX serves it and the API from the **same origin** (see "Web UI and Reverse Proxy" below)
- If a front end on another origin is ever added, allow only its exact origin, at the gateway or with an explicit allow-list

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

### Web UI and Reverse Proxy (NGINX)

- **Same origin:** NGINX serves the UI and proxies `/api/`, `/docs` and `/openapi.json` to `eta-api:8000`, so the browser never makes a cross-origin call and **CORS stays disabled**
- **API not published:** in Compose, `eta-api` has no host port (`expose` only); `/health`, `/ready` and `/redoc` are not reachable from outside
- **Client IP:** NGINX **overwrites** `X-Forwarded-For` with `$remote_addr` (never appends), and only the proxied `eta-api` container runs with `TRUST_PROXY_HEADERS=true`. A client-supplied `X-Forwarded-For` is discarded, so it can't dodge or poison the per-IP rate limit. Keep `TRUST_PROXY_HEADERS=false` anywhere the API is reachable directly
- **Headers on every response:** strict `Content-Security-Policy` (`default-src 'self'`, no inline script or style, `frame-ancestors 'none'`), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy`, `Cross-Origin-Opener-Policy: same-origin`; `server_tokens off`
- **`/docs` exception:** Swagger UI gets a relaxed CSP (inline script + `cdn.jsdelivr.net`); set `DOCS_ENABLED=false` to remove it
- **Container:** `nginxinc/nginx-unprivileged` (UID 101, port 8080), read-only filesystem with a `/tmp` tmpfs, `no-new-privileges`, 128 MB memory limit, 16 KB request-body limit
- **Rendering:** API data is inserted with `textContent` only; the README is rendered with raw HTML escaped and relative links shown as text
- **README is public:** the image serves `README.md` at `/README.md`, so it must never contain secrets or internal hostnames
- **Third-party code:** only `marked` 18.1.3, vendored (no CDN at runtime); review its release notes before upgrading
- **Browser storage:** only the theme (`localStorage`) and this session's ticket list (`sessionStorage`); nothing sensitive is stored

### Model Files

- `models/*.joblib` is a pickle: loading it can execute code. Load only models you trained yourself; never accept model files from untrusted sources
