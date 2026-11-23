# 04 — Always-Positive ETA

Chronological record of prompts and clarifying Q&A (MCQs). Assistant responses are excluded.
✅ marks the selected option.

---

## 1. Prompt

```text
can you refer the attached screenshot, and trying to change the number of years of experience to 15, and the ETA seems to be estimated as 0 Hours, which is NOT possible. I want you to analyze and recommend me where the model is to be tweaked so the minimum hours always calculated.

Do you get my concerns?
```

(Screenshot: Register Ticket, S1 Firewalls, Gold, EMEA, Phone, 4 devices, 40 months, 1 prior ticket, 15 years' experience, 20 min first response → "0 h".)

---

## 2. Analysis (summary)

- Raw linear-regression prediction for the ticket: **−6.3 h**, clipped to 0 by the API
- Root cause: additive model; intercept 29.8 h, S1 −26.6 h, experience −1.29 h per year for every severity, while real S1 tickets take 0.9–11.7 h (median 2.3 h)
- 14 of 971 test and 58 of 3,880 training predictions were negative; S1 MAE 5.45 h

| Option (same split) | MAE | RMSE | R² | Negative | S1 MAE | Ticket |
|---|---|---|---|---|---|---|
| Linear regression (0.4.0) | 18.47 | 25.04 | 0.198 | 14 | 5.45 | −6.3 → 0 h |
| Linear + severity floor | 18.38 | 25.02 | 0.200 | 0 | 3.66 | 0.9 h |
| Linear on log(hours) | 17.45 | 25.80 | 0.149 | 0 | 1.72 | 1.9 h |
| **Gamma GLM, log link** | 18.27 | 24.94 | 0.205 | 0 | 1.76 | 2.3 h |
| Gradient boosting | 18.55 | 25.66 | 0.158 | 3 | 3.28 | 2.4 h |

---

## 3. Q&A

**Q1. Which model change should fix the negative/zero ETAs?**

- ✅ **Gamma GLM, log link (Recommended)** — Always > 0; MAE 18.27, RMSE 24.94, R² 0.205 (all better than linear).
- **Linear on log(hours)** — Best MAE and S1 error, but RMSE and R² worse.
- **Keep linear + floor only** — ETA stops at 0.9 h, but S1 stays wrong.
- **Gradient boosting** — No better here; still 3 negative predictions.

**Q2. Should the API also enforce a minimum ETA as a safety net?**

- ✅ **Per-severity floor (Recommended)** — 1st percentile of training hours per severity, stored in metadata.
- **Single global floor** — One minimum for all severities.
- **No floor** — Rely on the model alone.

**Q3. How should the reference notebook reflect the fix?**

- ✅ **Add a short section (Recommended)** — Keep linear regression; append negative ETAs → Gamma GLM → comparison.
- **Replace the model** — Swap LinearRegression in the existing cells.
- **Leave notebook unchanged** — API and notebook would diverge.

**Q4. The API accepts values beyond the training range (e.g. experience up to 50, training max 20). What should be done?**

- **Keep ranges, rely on GLM (Recommended)** — No contract change.
- ✅ **Clamp to training range** — Cap inputs at the training min/max before predicting. *(non-obvious; revisited in §4)*
- **Tighten validation** — 422 outside the training range; breaking change.

---

## 4. Q&A — Non-Obvious Choice Revisited

**Q1. How should inputs outside the training range be handled?**

- **Keep clamp + log it** — Clamp and log a warning only.
- **Switch to no clamp** — Rely on the GLM.
- ✅ **Clamp + tell the client** — Clamp, and add an optional `adjusted_inputs` list to the response (additive, non-breaking), shown in the UI.

---

## 5. Prompt

```text
I would like to update the API and UI related to the current decisions we have made.
```

**Q1. Which parts of the plan should be implemented now?**

- **API + UI + model/training (Recommended)** — Notebook section later.
- ✅ **Everything in the plan** — Also the notebook section and lecture notes.
- **API + UI only, no retrain** — Floor and clamping on the linear model.

---

## 6. Outcome (v0.5.0)

- Gamma GLM served; screenshot ticket → **2.3 h** (fixed S1 ETA 4 h)
- Minimum ETA: S1 0.9 · S2 6.9 · S3 8.3 · S4 11.6 h; inputs clamped to the training range and returned as `adjusted_inputs` (e.g. experience 35 → 20, ETA 1.9 h), logged with the `request_id`, shown in the UI
- Notebook section 17 (`[C50]`–`[C53]`) reproduces the comparison; lesson learned: `TweedieRegressor`'s default `alpha=1.0` penalty must be set to `0.0`
