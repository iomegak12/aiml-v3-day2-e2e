# 02 — Model REST API

Chronological record of prompts and clarifying Q&A (MCQs). Assistant responses are excluded.
✅ marks the selected option.

---

## 1. Prompt

```text
can you work on this given prompt to build a back-end REST API out of a ML Model?

<full prompt: docs/prompts/001-model-rest-api-prompt.md>

Let me know what you have understood, in bulleted points (titles only), and let's have a debate on these MCQs based QAs so we are aligned in what we want to achieve.
```

- Full prompt (role, goal, ML modules, API package, OpenAPI, RFC 9457, rate limiting, probes, CORS, `.env`, dependencies, Docker, tests, docs, acceptance criteria): [prompts/001-model-rest-api-prompt.md](prompts/001-model-rest-api-prompt.md)

---

## 2. Q&A

**Q1. The prompt says day2 is in a uv workspace rooted at demonstrations/, but there is no root pyproject.toml and uv.lock lives in day2/. How should the lock export work?**

- ✅ **Standalone day2 (Recommended)** — Treat day2 as its own uv project; export with `uv export --frozen --no-default-groups --no-emit-project -o requirements.lock` (no `--package`).
- **Create a workspace root** — Add demonstrations/pyproject.toml with `[tool.uv.workspace]`, move the lock up. Touches day1.
- **Stop and let me fix** — Pause until the workspace is set up.

**Q2. CHANGELOG has only [Unreleased] and pyproject is 0.1.0, but the prompt asks for a 0.3.0 entry. How should versions be handled?**

- **0.2.0 + 0.3.0 (Recommended)** — Release the current [Unreleased] notebook work as 0.2.0 and the API as 0.3.0.
- ✅ **Fold into 0.3.0** — One 0.3.0 entry containing both the notebook work and the API.
- **Keep Unreleased** — Leave [Unreleased] and add 0.3.0 above it.

> Note: the question's premise was partly wrong — CHANGELOG already had a 0.2.0 entry (pyproject was still 0.1.0). Folding [Unreleased] + API into 0.3.0 therefore keeps every milestone.

**Q3. Should this work get a matching prompt and Q&A log (docs/02-…)?**

- **Yes, docs/02-… (Recommended)** — Mirror docs/01 with the prompt reference and decisions.
- ✅ **No log** — Only the docs listed in the prompt. *(changed in §3)*

**Q4. How far should the acceptance criteria be verified?**

- ✅ **Full check (Recommended)** — Train, pytest, live uvicorn + curl spot checks, `docker compose up --build`, healthy + non-root, report image size. No commits.
- **Full check + commit** — Same, then one commit on a feature branch.
- **Train + pytest only** — Skip live server and Docker checks.

---

## 3. Q&A — Non-Obvious Choices Revisited

**Q1. Versioning: keep "Fold into 0.3.0" or switch to 0.2.0 + 0.3.0?**

- **Switch to 0.2.0 + 0.3.0**
- ✅ **Keep fold into 0.3.0**

**Q2. Prompt log: keep "No log" or create docs/02-model-rest-api.md?**

- ✅ **Switch to docs/02 log**
- **Keep no log**

---

## 4. Prompt

```text
can you add makefile to the current workspace to
- build container image
- start containers
- stop containers
- test a sample request to consume model predictions
```

---

## 5. Q&A

**Q1. How should the 'test a sample request' target call the prediction API?**

- ✅ **curl + JSON file (Recommended)** — Payload in `data/sample_prediction_request.json`, sent with `curl -d @file`; same in cmd, PowerShell and Git Bash.
- **Python script** — `scripts/predict_sample.py` (urllib) with a unit test.
- **Inline curl JSON** — JSON inside the Makefile; quoting breaks under cmd.

**Q2. The image build needs a trained model. What should the build target do?**

- ✅ **Train if missing (Recommended)** — `build` depends on the model file; trains only when absent, then `docker compose build`.
- **Build only** — Dockerfile fails with its clear message if there is no model.
- **Always retrain** — Retrain before every build.

**Q3. Should 'start' wait until the container reports healthy?**

- ✅ **Wait for healthy (Recommended)** — `docker compose up -d --wait`.
- **Detach immediately** — `docker compose up -d`.

**Q4. Extra targets besides build, start, stop and the sample request? (multi-select)**

- ✅ **help (default)**
- ✅ **train / test / lock**
- ✅ **logs / status**
- **None**
