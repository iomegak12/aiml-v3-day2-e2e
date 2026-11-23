# 002 — Web UI for the ETA REST API (build prompt)

> **Decided after review:** themes = **NetCore Light** (`netcore-light`, the "NetCore Blue" palette, default) and **NetCore Dark** (`netcore-dark`), with a Light/Dark toggle in the header. Both palettes are in [docs/design/theme-options.html](../design/theme-options.html). This replaces the earlier "all 5 themes + switcher" decision.

---

## 1. Role and Context

You are a senior front-end and platform engineer working in the `day2/` project of an ML training course. Follow `AGENTS.md` exactly: modular code, reusable scripts in `scripts/`, data in `data/`, docs in `docs/`, mandatory unit tests, README/CHANGELOG updated with every change. The decisions in this prompt are final; ask multiple-choice questions only if something is genuinely blocking.

### What already exists

- **Project:** standalone uv project `day2/` (Python ≥ 3.12, `uv.lock` in `day2/`), package `netcore_tac` in `src/`.
- **REST API** (`src/netcore_tac/api/`, v0.3.0): FastAPI + uvicorn, Docker Compose service `eta-api` (container port 8000, currently published as `${PORT:-8000}:8000`).

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/predictions` | Body `TicketIn` → `PredictionOut`; rate limited |
| GET | `/health`, `/ready` | Probes; not rate limited |
| GET | `/docs`, `/openapi.json` | Swagger UI (loads assets from `cdn.jsdelivr.net`) and schema |

- **`TicketIn`** (`src/netcore_tac/api/schemas.py`, `extra="forbid"`):

| Field | Type / range |
|-------|--------------|
| `created_at` | ISO-8601 datetime (weekend flag uses the wall-clock time as sent) |
| `product_family` | string 1–50 chars; known: Firewalls, Routers, SD-WAN, Switches, Wireless; unseen allowed |
| `severity` | `S1` · `S2` · `S3` · `S4` |
| `customer_tier` | `Platinum` · `Gold` · `Silver` |
| `region` | `AMER` · `EMEA` · `APJC` |
| `channel` | `Email` · `Phone` · `Portal` |
| `devices_affected` | int 1–1000 |
| `software_version_months` | int 0–240 |
| `prior_tickets_90d` | int 0–100 |
| `engineer_experience_years` | float 0–50 or `null` |
| `first_response_minutes` | float 0–10080 or `null` |

- **`PredictionOut`:** `predicted_hours` (≥ 0, 1 dp), `model_version`, `request_id` (also `X-Request-ID` header).
- **Errors:** RFC 9457 `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`, `request_id`; 422 adds `errors: [{field, message}]`; 429 sends `Retry-After` (seconds); 503 = model not loaded.
- **Rate limit:** 100 requests / 60 s per client IP, then a 30 s block; `RateLimit-Limit/Remaining/Reset` headers. Client IP is `request.client.host`, or the first `X-Forwarded-For` address when `TRUST_PROXY_HEADERS=true`.
- **CORS:** disabled by design (`SECURITY.md`). Keep it that way.
- **Fixed per-severity ETA** (the business baseline): S1 4 h, S2 24 h, S3 48 h, S4 72 h.
- **Makefile:** `help`, `build`, `start`, `stop`, `status`, `logs`, `predict`, `train`, `test`, `lock`; recipes are shell-neutral (cmd, PowerShell, Git Bash).
- **Theme source of truth:** [docs/design/theme-options.html](../design/theme-options.html) — `[data-theme]` token blocks (NetCore Blue = Light, NetCore Dark, plus four reference themes), mock screens, sample chips and contrast checks.
- **Tooling:** Node 22 is available (built-in `node --test`); Docker Desktop with Compose v2.

---

## 2. Goal and Non-Goals

**Build:** a static web UI (plain HTML, CSS, JavaScript ES modules) served by NGINX, which also reverse-proxies the API on the same origin. Two pages: **Home** (README rendered as HTML) and **Register Ticket** (form + sample chips → ETA). Own Dockerfile, Compose service, Makefile targets, unit tests and docs.

**Out of scope (do not build):** frameworks or bundlers (React, Vue, Vite, Tailwind…), npm dependencies, CDN assets, authentication, CORS, server-side persistence or a database, editing/deleting tickets, i18n, integration or end-to-end tests, changes to the Python API code.

---

## 3. Agreed Decisions (do not re-ask)

| Topic | Decision |
|-------|----------|
| Location | `day2/web/` |
| API access | Same-origin NGINX reverse proxy → `eta-api:8000`; CORS stays disabled |
| Exposed via NGINX | `/api/`, `/docs`, `/openapi.json`; API `/health` and `/ready` stay internal |
| API port | No longer published to the host (Compose `expose` only) |
| Client IP | NGINX overwrites `X-Forwarded-For` with `$remote_addr`; `eta-api` gets `TRUST_PROXY_HEADERS=true` |
| Home page | NGINX serves a copy of `README.md`; vendored `marked` (ESM build, no CDN) renders it at runtime |
| Register | ETA card (vs fixed severity ETA) + "Registered this session" list in `sessionStorage`; nothing server-side |
| Themes | NetCore Light + NetCore Dark only; header toggle; choice saved in `localStorage`; no automatic OS light/dark switching |
| Default theme | `netcore-light` |
| Web port | `WEB_PORT`, default **80**, overridable (e.g. `8080`) |
| JS tests | `node --test` (Node 22 built-in), no npm packages |
| Makefile | Whole-stack `build/start/stop/status/logs` + `build-api`, `build-web`, `test-web`; `predict` goes through NGINX |

---

## 4. Folder Layout

```
web/
├── Dockerfile                    # nginx-unprivileged image with site + README
├── Dockerfile.dockerignore       # build-context allow-list for this Dockerfile
├── nginx/
│   ├── default.conf              # server block: static site + /api, /docs, /openapi.json proxy
│   ├── security-headers.conf     # shared add_header lines (included per location)
│   └── proxy.conf                # shared proxy_* settings for the API locations
└── site/
    ├── index.html                # Home
    ├── register.html             # Register Ticket
    ├── css/
    │   ├── tokens.css            # netcore-light + netcore-dark blocks from theme-options.html
    │   ├── base.css              # reset, typography, layout, focus styles
    │   └── components.css        # header, nav, cards, chips, form, buttons, badges, tables, banners, readme
    ├── js/
    │   ├── config.js             # constants: API path, FIXED_ETA_HOURS, FIELD_LIMITS, THEMES, DEFAULT_THEME, storage keys
    │   ├── payload.js            # form values → TicketIn payload; client-side checks
    │   ├── chips.js              # 5 sample tickets → form values (injected clock)
    │   ├── eta.js                # duration formatting, comparison with the fixed ETA
    │   ├── api.js                # POST /api/v1/predictions, problem+json parsing, timeout
    │   ├── history.js            # session list (injected storage, in-memory fallback)
    │   ├── theme.js              # resolve / load / save / apply theme (injected storage)
    │   ├── markdown.js           # marked configuration: link policy, raw-HTML escaping
    │   ├── theme-init.js         # classic (non-module) script in <head>: apply saved theme before paint
    │   ├── layout.js             # shared header: light/dark toggle (DOM glue)
    │   ├── home.js               # Home controller (DOM glue)
    │   └── register.js           # Register controller (DOM glue)
    └── vendor/
        ├── marked.esm.js         # pinned marked ESM build (exact version in the file header + README)
        └── marked.LICENSE        # its MIT licence
tests/web/                        # node --test unit tests (*.test.mjs), one per pure module
```

- Pure modules (`config`, `payload`, `chips`, `eta`, `api`, `history`, `theme`, `markdown`) hold **all** logic and take their dependencies (clock, storage, fetch, document) as parameters so Node can test them without a DOM.
- Controllers (`layout`, `home`, `register`) and `theme-init.js` are thin DOM glue only, with no business logic. They have no unit tests (that would need jsdom, an npm dependency). They're covered by the acceptance checks in §14. Record this exception in `CONTRIBUTING.md`.

---

## 5. NGINX

**Base image:** `nginxinc/nginx-unprivileged:1.30.6-alpine` (stable branch; an exact patch tag at least two weeks old). It runs as UID 101 and listens on 8080, with temp files and the pid under `/tmp`.

**`default.conf`:**

- `listen 8080;` `server_tokens off;` `root /usr/share/nginx/html;` `index index.html;` `charset utf-8;`
- `client_max_body_size 16k;` (one ticket is < 1 KB)
- `gzip on;` for `text/css`, `application/javascript`, `application/json`, `application/problem+json`, `text/markdown`
- `types { text/markdown md; }` added to the defaults so `/README.md` is served as UTF-8 markdown
- **Dynamic upstream** (so NGINX starts even when the API is briefly down, and follows container IP changes): `resolver 127.0.0.11 valid=10s ipv6=off;` and `set $api_upstream http://eta-api:8000;` then `proxy_pass $api_upstream;` (no URI part, so the request URI passes unchanged)
- `location = /healthz` → `return 200 "ok\n";` (`access_log off`, `text/plain`), used by the container healthcheck
- `location /api/`, `location = /docs`, `location = /openapi.json` → proxy to `$api_upstream` with:
  - `proxy_set_header Host $host;`
  - `proxy_set_header X-Forwarded-For $remote_addr;` (**overwrite, never append**, so clients can't spoof their IP)
  - `proxy_set_header X-Forwarded-Proto $scheme;`
  - `proxy_connect_timeout 3s; proxy_read_timeout 15s;`
  - Upstream headers (`X-Request-ID`, `Retry-After`, `RateLimit-*`, `Content-Type`) pass through unchanged
  - `proxy_intercept_errors off` (the API's problem+json bodies reach the browser)
- When the upstream is unreachable, return a 502/504 **problem+json** body (`error_page 502 503 504 = @api_down;` with a JSON `return` and `default_type application/problem+json`), type `https://netcore.example/problems/api-unavailable`
- `location /` → `try_files $uri $uri/ =404;`; HTML, CSS, JS and README use `Cache-Control: no-cache` (no hashed filenames)
- Do **not** proxy `/redoc`, `/health` or `/ready`

**`security-headers.conf`** (`include` it inside every `location` that sets headers, because `add_header` isn't inherited once a location defines its own):

- `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`
- `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`, `Cross-Origin-Opener-Policy: same-origin`
- Use `always` so error responses carry them too
- `/docs` only gets a relaxed CSP: `script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com` (Swagger UI needs these)
- Never add `Access-Control-*` headers

**Consequences for the site:** no inline `<script>`, no inline event handlers, no `style="…"` attributes (setting styles from JS through the CSSOM is fine).

---

## 6. Web Dockerfile and Build Context

- **Build context:** `day2/` (needed for `README.md`), with `dockerfile: web/Dockerfile`.
- **`web/Dockerfile.dockerignore`:** BuildKit uses it instead of the root `.dockerignore` for this Dockerfile. Content: `*` then `!web/nginx/`, `!web/site/`, `!README.md`.
- **Root `.dockerignore`:** add `web/` so the API image never contains the site.
- **Steps:**
  1. `FROM nginxinc/nginx-unprivileged:<pinned>-alpine`
  2. `COPY web/nginx/default.conf /etc/nginx/conf.d/default.conf`
  3. `COPY web/nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf`
  4. `COPY web/site/ /usr/share/nginx/html/`
  5. `COPY README.md /usr/share/nginx/html/README.md`
  6. `RUN nginx -t` (works at build time because the upstream is a variable)
  7. Stay `USER 101`, `EXPOSE 8080`
  8. `HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --start-interval=2s CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1`
- **Files must be owned by root and read-only** for the nginx user (the default after `COPY`).
- **Report the final image size** in the README.

---

## 7. Pages

### Shared layout (both pages)

- Skip link → `#main`
- Header (`--header-bg`):
  - Brand "NetCore TAC ETA"
  - Nav: **Home** · **Register Ticket**, with `aria-current="page"` on the active link
  - External link **API docs** → `/docs`
  - Theme toggle button ("Theme: Light" / "Theme: Dark", `aria-pressed`)
- Footer: "Predictions are estimates from a linear-regression model (test MAE ≈ 18.5 h)" + link to `/docs`
- `<head>`: `theme-init.js` (classic script, first) then the CSS files; module scripts at the end with `type="module"`
- Responsive down to 360 px with no horizontal page scroll; wide tables scroll inside their own container

### Home — `index.html`

- On load, `fetch('/README.md')` and render with `marked` through `markdown.js` into `<article class="readme">`.
- **Link policy** (`markdown.js`):
  - `#anchors` → kept (headings get slug ids)
  - `http(s)://` → `target="_blank" rel="noopener noreferrer"`
  - Relative links to repo files (e.g. `docs/…`, `SECURITY.md`) → rendered as plain text with the path in `<code>`, because the image doesn't serve them
- **Raw HTML** in the markdown is escaped, never rendered.
- States:
  - Loading: skeleton or "Loading README…" text
  - Error: a message with a **Retry** button (shown on fetch failure or non-200)
- Code blocks use `--code-bg` / `--code-text`; tables get borders and a horizontal-scroll wrapper.

### Register Ticket — `register.html`

Layout as in the theme preview: form card (left) and result + session list (right), stacked on small screens.

**1. Sample chips (5)** above the form, toggle buttons with `aria-pressed`. Clicking a chip fills every field. Labels and values:

| Chip | Values |
|------|--------|
| `S1 · Core router outage` | Routers, S1, Platinum, AMER, Phone, 25 devices, 18 months, 3 prior, 9.5 y, 5 min; created **today 02:10** |
| `S2 · Weekend firewall` | Firewalls, S2, Gold, EMEA, Phone, 4, 40, 1, 6.5, 20; created **most recent Saturday 10:30** |
| `S3 · Old switch software` | Switches, S3, Silver, APJC, Portal, 12, 60, 5, 3, 95; created **now** |
| `S4 · Wireless question` | Wireless, S4, Silver, EMEA, Email, 1, 6, 0, 12, 240; created **now** |
| `Unknown product, missing data` | Optical Transport, S2, Gold, AMER, Portal, 8, 30, 2, *(blank)*, *(blank)*; created **now** |

**2. Form fields** (labels as in the preview):
- `created_at`: `datetime-local`, default **now** (minutes precision)
- `product_family`: text + `<datalist>` of the 5 known families, `maxlength=50`
- Selects for severity, tier, region and channel
- Numbers with `min`/`max`/`step` from `FIELD_LIMITS`
- Experience and first response may be blank; hint "Leave blank if unknown"

**3. Submit "Get ETA":**
- Runs client checks first (`payload.js`, same limits as `TicketIn`) and shows inline messages without calling the API.
- Then `api.predict(payload)`. While waiting, the button shows "Predicting…" and is disabled.
- Requests time out after 10 s (`AbortController`).

**4. Result card** (`aria-live="polite"`; focus moves to its heading):
- Big `32.5 h`, with `≈ 1 d 8.5 h to resolve` beneath it
- Pills: `Fixed S2 ETA: 24 h` and `+8.5 h vs fixed` (or `−3.2 h vs fixed`)
- Meta line: `model 0.3.0 · request <request_id>`

**5. Errors** (from `api.js` results):
- **422:** map `errors[].field` to inputs (`aria-invalid="true"`, message below the field, error summary at the top of the form linking to each field). Unknown fields go in the summary.
- **429:** warning banner "Too many requests. Try again in N s" that counts down from `Retry-After`; the submit button stays disabled until it reaches 0.
- **503:** "The prediction model isn't ready. Try again shortly."
- **502/504, other 5xx, network failure or timeout:** generic error banner, including `request_id` when present.
- Never insert API text with `innerHTML`; always use `textContent`.

**6. "Registered this session"** list:
- Each success adds a row: `WEB-0001`, … (sequential per browser session), created time, severity badge, product, tier, ETA, fixed ETA, Δ.
- Newest first, maximum 20 rows; **Clear list** button; empty state "No tickets registered yet".
- Stored in `sessionStorage`; if storage isn't available, use an in-memory list for the page lifetime.

---

## 8. JavaScript Modules (pure, unit-tested)

| Module | Exports (indicative) |
|--------|----------------------|
| `config.js` | `API_PREDICT_PATH = "/api/v1/predictions"`, `FIXED_ETA_HOURS`, `FIELD_LIMITS`, `KNOWN_PRODUCTS`, `THEMES` (id + label), `DEFAULT_THEME`, `THEME_STORAGE_KEY = "netcore-tac-theme"`, `HISTORY_STORAGE_KEY`, `HISTORY_MAX = 20`, `REQUEST_TIMEOUT_MS = 10000` |
| `payload.js` | `formToPayload(values)` (trim strings; numbers via `Number`; blank optional numbers → `null`; `datetime-local` → `YYYY-MM-DDTHH:mm:00`); `validatePayload(payload)` → `{field: message}` |
| `chips.js` | `SAMPLE_TICKETS`; `chipToFormValues(chip, now)` (resolves "today 02:10", "most recent Saturday 10:30", "now") |
| `eta.js` | `formatDuration(hours)` → `"1 d 8.5 h"` / `"16.3 h"`; `compareWithFixed(severity, hours)` → `{fixed, delta, label}` |
| `api.js` | `predict(payload, {fetchImpl = fetch, timeoutMs})` → `{ok: true, data, requestId}` or `{ok: false, kind: "validation" \| "rate-limited" \| "not-ready" \| "unavailable" (502/504) \| "server" \| "network" \| "timeout", status, problem, fieldErrors, retryAfter, requestId}`; `parseProblem(response)` |
| `history.js` | `createHistory(storage, {key, max})` → `{add(entry), list(), clear(), nextId()}`; survives a missing or throwing storage |
| `theme.js` | `resolveTheme(stored, themes, fallback)`, `loadTheme(storage)`, `saveTheme(storage, id)`, `applyTheme(doc, id)` (sets `data-theme` on `<html>`), `toggleTheme(id)`; all storage access in try/catch |
| `markdown.js` | `createMarked(marked)` / `renderReadme(markdown, marked)` applying the link policy, slug ids and raw-HTML escaping |

---

## 9. Theming and Accessibility

- `css/tokens.css`: `[data-theme="netcore-light"]` (the NetCore Blue tokens) and `[data-theme="netcore-dark"]` (the NetCore Dark tokens) from `docs/design/theme-options.html` (tokens such as `--bg`, `--surface`, `--primary`, `--header-bg`, `--sev-s1-bg/fg` … `--code-text`, plus `color-scheme`). All other CSS uses only these tokens, with no hard-coded colours.
- `<html data-theme="netcore-light">` in the markup. `theme-init.js` applies the saved theme before first paint, and the header toggle switches and saves it. An unknown saved value falls back to the default.
- Meet **WCAG 2.2 AA:**
  - Contrast: text ≥ 4.5:1; input borders and focus ring ≥ 3:1 (already checked in the preview).
  - Visible `:focus-visible` ring using `--focus`.
  - Every input has a `<label>`; chips are `<button>`s with `aria-pressed`.
  - Errors are linked with `aria-describedby`; the result has `aria-live="polite"`.
  - Never use colour alone (severity badges show the text S1–S4).
- Respect `prefers-reduced-motion` (no transitions when set).

---

## 10. Docker Compose

Update `docker-compose.yml`:

```yaml
services:
  eta-api:
    # …existing build, env_file, healthcheck, hardening unchanged…
    environment:
      HOST: 0.0.0.0
      PORT: "8000"
      TRUST_PROXY_HEADERS: "true"      # NGINX overwrites X-Forwarded-For with the real client IP
    expose:
      - "8000"                          # internal only; replaces the old `ports:` mapping
  web:
    build:
      context: .
      dockerfile: web/Dockerfile
    image: netcore-tac-eta-web:0.4.0
    ports:
      - "${WEB_PORT:-80}:8080"
    depends_on:
      eta-api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]
      interval: 30s
      timeout: 3s
      start_period: 5s
      start_interval: 2s
      retries: 3
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - "no-new-privileges:true"
    mem_limit: 128m
```

- `.env.example`: add `WEB_PORT=80` with a comment ("host port for the web UI; use 8080 if 80 is taken"). Note that `PORT` now only matters for running the API locally with uvicorn.
- `TRUST_PROXY_HEADERS` stays `false` by default in `.env.example` (local uvicorn); Compose sets it for the proxied container only.

---

## 11. Makefile

Keep recipes shell-neutral (cmd, PowerShell, Git Bash). Add `WEB_PORT ?= 80` and `WEB_URL ?= http://127.0.0.1:$(WEB_PORT)`; `.env` is already included.

| Target | Behaviour |
|--------|-----------|
| `help` (default) | Lists every target |
| `build` | Trains the model if missing, then `docker compose build` (both images) |
| `build-api` | Trains if missing, then `docker compose build eta-api` |
| `build-web` | `docker compose build web` |
| `start` | Trains if missing, then `docker compose up -d --wait` (both services healthy) |
| `stop` / `status` / `logs` | `down` / `ps` / `logs -f` for the whole stack |
| `predict` | Same curl, sent to `$(WEB_URL)/api/v1/predictions` (through NGINX) |
| `test` | `uv run pytest` (unchanged) |
| `test-web` | `node --test "tests/web/*.test.mjs"` |
| `train`, `lock` | Unchanged |

---

## 12. Tests

- **Folder:** `tests/web/*.test.mjs` using `node:test` + `node:assert/strict`; import the site modules by relative path. No npm, no DOM, no network.
- **`config`:** fixed ETAs, field limits identical to `TicketIn`, the two NetCore themes, light by default.
- **`payload`:**
  - Types and nulls; `datetime-local` conversion
  - Each limit violated → message for that field
  - The `data/sample_prediction_request.json` values produce an identical payload
- **`chips`:**
  - 5 chips, each filling every field
  - "most recent Saturday 10:30" correct for every weekday, including a Saturday before and after 10:30
  - "today 02:10" and "now" with a fixed clock
  - Blank optional fields on the unknown-product chip
- **`eta`:**
  - `formatDuration` boundaries (0, 0.04, 23.9, 24, 32.5, 100)
  - `compareWithFixed` sign and label per severity
- **`api`** (fake `fetchImpl`):
  - 200 → data + `requestId` from the header
  - 422 → `fieldErrors` map
  - 429 → `retryAfter` from the header
  - 503, 500 and a 502 problem body
  - Non-JSON error body
  - Rejected fetch → `network`; abort → `timeout`
  - Request is POST with a JSON body and `Content-Type`
- **`history`** (fake storage):
  - Ids increment; newest first; capped at 20; `clear`
  - Corrupt JSON → empty list
  - Throwing storage → in-memory fallback
- **`theme`:**
  - Resolve a valid, unknown or null stored value
  - Save and load round trip
  - Throwing storage doesn't throw
  - `applyTheme` sets `data-theme` on a fake document; `toggleTheme` switches light/dark
- **`markdown`:**
  - Anchor, external and relative-file link handling
  - Raw `<script>` escaped
  - Heading slug ids
- **Existing suite:** `uv run pytest` must still pass. Update `tests/test_sample_request.py` only if needed.

---

## 13. Documentation

- **`README.md`:**
  - Web UI section: architecture diagram (browser → NGINX :80 → `/api`, `/docs` → `eta-api` :8000), pages, light/dark toggle, `make` targets, URLs (`http://localhost` / `http://localhost:${WEB_PORT}`)
  - Updated project structure, image sizes, marked version
  - Update every example that used `http://127.0.0.1:8000` with Compose to go through the web port; local uvicorn examples stay on 8000
- **`SECURITY.md`:**
  - NGINX reverse proxy and same-origin design (CORS still disabled)
  - `X-Forwarded-For` overwrite + `TRUST_PROXY_HEADERS=true` only for the proxied container
  - CSP and the other security headers (and the relaxed `/docs` CSP)
  - Non-root, read-only NGINX
  - API port no longer published
  - README served publicly, so it must never contain secrets
  - Vendored `marked` with a pinned version
- **`TROUBLESHOOTING.md`:**
  - Port 80 already in use (IIS, `W3SVC`, Skype, WSL) → `WEB_PORT=8080`
  - 502 Bad Gateway / "API unavailable" → `make status`, `make logs`
  - Home shows "Could not load README"
  - Theme not remembered in private browsing
  - CSP errors in the console after adding inline code
  - `node --test` not found → install Node ≥ 22
- **`CONTRIBUTING.md`:** how to edit `web/site`, run `make test-web`, rebuild with `make build-web start`, the no-inline-code CSP rule, the controller unit-test exception, and how to upgrade the vendored `marked`.
- **`CHANGELOG.md`:** a `0.4.0` entry; bump `pyproject.toml` to `0.4.0`.
- **`AGENTS.md` folder table + `.github/copilot-instructions.md` summary:** add `web/` ("Web UI: NGINX config and static site").
- **`docs/03-web-ui.md`:** append the build session's prompts and Q&A.

---

## 14. Acceptance Criteria

- [ ] `make build` builds both images; `make start` returns with **both** services healthy; the web container runs as UID 101 on a read-only filesystem.
- [ ] `http://localhost` (or `:WEB_PORT`) shows Home with the README rendered (headings, tables, code blocks), relative repo links shown as text, and no console or CSP errors.
- [ ] Register Ticket: each chip fills the form; **Get ETA** shows the ETA card with the fixed-ETA comparison, `model_version` and `request_id`; the row appears in "Registered this session" and survives a page reload in the same tab.
- [ ] Invalid input caught on the client never reaches the API; a server-side 422 (e.g. forced via the console) shows inline field errors.
- [ ] Over 100 predictions within 60 s → a banner counts down from 30 and the button stays disabled until it reaches 0; two different client IPs are limited separately (check with curl and different `X-Forwarded-For` values: the spoofed header is ignored because NGINX overwrites it).
- [ ] Stopping `eta-api` → the UI shows "API unavailable" (problem+json 502/504 from NGINX) and recovers after a restart without restarting `web`.
- [ ] The Light/Dark toggle changes all colours instantly, persists across reloads, and an unknown saved value falls back to Light.
- [ ] `/docs` (Swagger UI) works through NGINX; `/health`, `/ready` and `/redoc` aren't reachable from the host; port 8000 isn't published.
- [ ] No `Access-Control-*` header on any response; every HTML response has the CSP and the other security headers.
- [ ] `make predict` works through NGINX.
- [ ] Usable at 360 px wide and by keyboard only (tab order, visible focus, chips toggle with Enter/Space).
- [ ] `make test-web` and `uv run pytest` pass; all listed docs updated; image sizes reported.
