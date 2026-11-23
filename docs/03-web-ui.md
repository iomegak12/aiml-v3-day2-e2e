# 03 — Web UI

Chronological record of prompts and clarifying Q&A (MCQs). Assistant responses are excluded.
✅ marks the selected option.

---

## 1. Prompt

```text
Based on the current understanding of the REST API that we have built out of a ML Model, I want to now design and develop an UI to consume the REST API services for predictions.

- HTML, CSS and JavaScript should be fine
- NGINX based back-end to consume REST API services
- Home (Read the README contents and generate HTML contents)
- Register Ticket option to register a ticket and get ETA for the ticket
- In the form, generate few sample chips to quickly fill up the form details.
- The complete web application can be created in web folder of the root workspace
- Dockerfile
- update Docker compose
- update other markdown files
- update makefile also to build container images for web

Can you generate a detailed prompt using which the complete web application can be built? And also, I would like to have few design options with 4-5 color themes so I can pick a one which matches my requirements.

Do you get my points?

Let's have a quick debate on this (MCQs based QAs)
```

---

## 2. Q&A

**Q1. Where should the web/ folder live?**

- ✅ **day2/web/ (Recommended)** — Inside this project; shares compose, Makefile, docs and AGENTS.md rules.
- **demonstrations/web/** — Parent folder; outside day2's git repo and rules.

**Q2. How should the browser reach the prediction API, given CORS is disabled?**

- ✅ **Same-origin proxy (Recommended)** — NGINX serves the UI and proxies /api/ to eta-api:8000; CORS stays disabled; only the web port is published.
- **Browser calls API directly** — Needs CORS enabled in the API, reversing the SECURITY decision.
- **Proxy + also publish API** — Proxy, but port 8000 also stays published.

**Q3. How should the Home page turn README.md into HTML?**

- ✅ **Render at runtime (Recommended)** — NGINX serves a copy of README.md; vendored marked renders it in the browser.
- **Convert at image build** — Converter stage produces static HTML; adds a build tool.
- **Hand-written HTML now** — Goes stale as the README changes.

**Q4. Ticket "registration": what happens after the ETA is returned?**

- ✅ **Show ETA + session list (Recommended)** — ETA vs fixed severity ETA, plus a list of this session's tickets in browser storage; no database.
- **Show ETA only** — Nothing kept.
- **Persist tickets server-side** — Needs a database; beyond the agreed scope.

---

## 3. Q&A

**Q1. Deliverable sequence for this step?**

- ✅ **Prompt + themes, then pause (Recommended)** — Write the prompt and theme previews; the user picks a theme and reviews before any build.
- **Prompt only** — Palettes described in the prompt; run it later.
- **Prompt + build now** — Build immediately with a default theme.

**Q2. How should the 4–5 colour themes be presented?**

- ✅ **Interactive preview page (Recommended)** — `docs/design/theme-options.html` with mock screens and a 5-theme switcher.
- **Preview page + private link** — Same page, also published as a private claude.ai artifact.
- **Palette table only** — Markdown token table; nothing visual.

**Q3. How should the JavaScript modules be unit-tested?**

- ✅ **node --test (Recommended)** — Pure ES-module functions tested with Node 22's built-in runner; no npm packages.
- **Jest / Vitest** — Adds package.json, node_modules and a lock file.
- **No JS tests** — Breaks the AGENTS.md rule.

**Q4. With API port 8000 no longer published, what should NGINX expose?**

- ✅ **/api/ + /docs + /openapi.json (Recommended)** — Predictions and Swagger UI through the web port; API probes stay internal.
- **/api/ only** — Smallest surface; no Swagger through NGINX.
- **Keep 8000 published too** — Two entry points; the direct one bypasses NGINX.

---

## 4. Q&A

**Q1. How should the Makefile handle the web image?**

- ✅ **Whole stack + per-service (Recommended)** — build/start/stop/status act on both; build-api, build-web, test-web; predict via NGINX.
- **Separate web-\* targets** — Existing targets stay API-only.

**Q2. Which host port should the web UI publish?**

- **8080 via WEB_PORT (Recommended)** — Rarely clashes.
- ✅ **80** — Clean URL; may clash with IIS or other local services. *(non-obvious; revisited in §5)*
- **8000** — Reuses the API's old port; confusing.

**Q3. Light/dark and theme application?**

- **Chosen theme + auto dark (Recommended)** — Ship the picked theme with light and dark variants that follow the OS.
- **Chosen theme, light only** — One fixed palette.
- ✅ **All themes + switcher** — Ship all 5 themes with a header picker. *(non-obvious; revisited in §5)*

---

## 5. Q&A — Non-Obvious Choices Revisited

**Q1. Web port: keep 80 or switch to 8080?**

- ✅ **Keep 80, overridable** — `WEB_PORT` defaults to 80; set `WEB_PORT=8080` if 80 is taken.
- **Switch to 8080**

**Q2. Theming: how should themes ship?**

- ✅ **Keep switcher, all 5** — All 5 themes in a header picker; choice saved in the browser.
- **Switcher + auto dark** — Each theme also follows the OS light/dark setting (10 palettes).
- **Switch to one + auto dark** — Only the picked theme, in light and dark.

---

## 6. Outputs

- Build prompt: [prompts/002-web-ui-prompt.md](prompts/002-web-ui-prompt.md)
- Theme options preview: [design/theme-options.html](design/theme-options.html) (open in a browser)
- Next: pick the default theme, review the prompt, then build

---

## 7. Prompt

```text
I prefer to use NetCore (Light and Dark Theme Options), and I have reviewed the prompt. We can go ahead and implement the same.
```

---

## 8. Q&A

**Q1. Which themes should the web UI ship?**

- ✅ **NetCore only: light + dark (Recommended)** — Drop the other 4 themes; NetCore Blue light + a new NetCore dark; header Light/Dark control.
- **All 5 + NetCore dark** — Keep the 5-theme switcher and add NetCore dark as a sixth option.

**Q2. How should light/dark be chosen?**

- **System default + toggle (Recommended)** — Follow the OS until the user picks Light or Dark.
- ✅ **Light default + toggle** — Always start light; the user can switch to dark, and the choice is saved. *(non-obvious: users whose OS is set to dark first see a light page; trade-offs shown, kept)*
- **Follow OS only** — No control in the header.

**Q3. Where should the NetCore dark palette come from?**

- ✅ **New NetCore Dark (Recommended)** — Derived from NetCore Blue, WCAG AA checked, added to the preview.
- **Reuse Midnight NOC** — Already checked, but cyan/lime accents don't match NetCore Blue.

**Q4. Accept the unit-test exception for the page scripts (layout, home, register)?**

- ✅ **Accept exception (Recommended)** — All logic in pure tested modules; DOM glue covered by acceptance checks; documented in CONTRIBUTING.
- **Add jsdom tests** — Adds package.json, node_modules and a lock file.

---

## 9. Outcome

- Web UI built in `web/` (v0.4.0); prompt `002` updated with the final theme decision
- Verified: both containers healthy; Home renders README; chips → ETA; client and server 422; 429 countdown; per-client rate limit through NGINX (spoofed `X-Forwarded-For` ignored); 502 problem+json when the API is down and recovery after restart; Light/Dark toggle persists; no horizontal scroll at 360 px; no `Access-Control-*` headers; `/health`, `/ready`, `/redoc` and port 8000 not reachable from the host
