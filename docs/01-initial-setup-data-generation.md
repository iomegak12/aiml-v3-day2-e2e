# 01 — Initial Setup & Data Generation

Chronological record of prompts and clarifying Q&A (MCQs). Assistant responses are excluded.
✅ marks the selected option.

---

## 1. Prompt

```text
My name is Ramkumar, am the training facilitator to training students on ML concepts (including Data Quality, EDA, Feature Engineering, Pipelines and Regression types of ML). My students are from Networking | Network Support to enterprise clients who are having 15+ YOE in the escalation and support management.

Before we proceed to doing any further activities, i want you to understand and analyze the document docs\business-use-case.txt at the workspace, which describes the business use case at a high level.

Let me know what you have understood, in bulleted points with a list of items - TITLES ONLY.
```

---

## 2. Prompt

```text
I want you to create a system instructions file, which is applicable to both GitHub copilot and Claude code which satisfies the following
- Do NOT assume anything on your own, always clarify with me if you have any doubts
- Do NOT generate any contents (scripts, commands, files, codes) unless I ask you to do so.
- Do NOT generate any detailed responses by default, until I ask you to do so. I always prefer as brief as possible. Bulleted Points. List of Items (With Titles Only)
- Whenever you ask me a question, I always prefer MCQs based QAs. Not in prose style.
- Whenever I select a Non-Obvious | Unusual option, I strongly recommend to see those options, pros/cons, why it should NOT be selected.
- I always prefer modularized code generated whenever we decide to generate source files
- Documentation should be kept in docs folder
- I prefer Unit Testing mandatorily to prove the concept is working. I defer NOT to introduce Integration Testing, Web Testing or any other testing by default, unless I ask you to do so.
- I prefer reusable scripts in scripts folder
- Any data is generated whether it's sample | synthetic, it should be under data folder
- I prefer to have the following files as part of my standard practices
a. .gitignore
b. README, TROUBLESHOOTING, CONTRIBUTING, CHANGE LOG, SECURITY, CODE OF CONDUCT
c. MIT LICENSE
d. keep .gitkeep files wherever applicable
- you should always update README markdown files as and when any further development takes place

Do you understand my initial thoughts before we proceed to further ML Development?
```

---

## 3. Q&A

**Q1. How should one instructions file serve both GitHub Copilot and Claude Code?**

- ✅ **AGENTS.md + thin pointers (Recommended)** — One source of truth in AGENTS.md. CLAUDE.md imports it (@AGENTS.md) and .github/copilot-instructions.md points to it. No duplicated rules.
- **Two duplicated files** — Same full content in CLAUDE.md and .github/copilot-instructions.md. Simple, but the copies can drift apart.
- **CLAUDE.md only + Copilot pointer** — Full rules in CLAUDE.md, and .github/copilot-instructions.md says to follow it.

**Q2. Which folder should the instructions apply to?**

- **demonstrations/ root (Recommended)** — Covers day1, day2 and later days. This folder appears to be the git repo root.
- ✅ **day2/ only** — Applies only to the Day 2 ML work.

**Q3. Should I also create the standard project files (README, LICENSE, .gitignore, docs/, scripts/, data/, tests/ with .gitkeep) now?**

- **Instructions file only (Recommended)** — Matches your rule of creating content only on request. Scaffold the project later as a separate step.
- ✅ **Instructions + full scaffold** — Create the instructions file and all standard files and folders in one go.

**Q4. Which unit testing framework should the instructions require?**

- ✅ **pytest (Recommended)** — The Python and ML standard, with simple fixtures. It fits your uv/pyproject setup.
- **unittest** — Built into Python with no extra dependency, but more verbose.

---

## 4. Q&A

**Q1. Having seen the pros and cons, do you keep both choices (day2-only scope + full scaffold now)?**

- ✅ **Keep both** — day2/ scope and full scaffold now.
- **Switch scope to root** — demonstrations/ root scope and full scaffold now.
- **Keep scope, instructions only** — day2/ scope; skip the scaffold for now.

**Q2. Who should be the copyright holder in the MIT LICENSE?**

- ✅ **Ramkumar (Recommended)** — Copyright (c) 2026 Ramkumar
- **NetCore (fictional)** — Copyright (c) 2026 NetCore. Only fits a fictional training context.
- **Generic placeholder** — <COPYRIGHT HOLDER> for you to fill in later.

**Q3. What contact should SECURITY.md and CODE_OF_CONDUCT.md use for reporting?**

- ✅ **Placeholder (Recommended)** — <security-contact@example.com> for you to replace. Keeps your personal email out of the repo.
- **Your Git email** — Use the email from your Git config.
- **GitHub issues only** — Report through repository issues; no email.

**Q4. pytest isn't in day2/pyproject.toml yet. Should the scaffold add it?**

- ✅ **Add as dev dependency (Recommended)** — Add pytest under [dependency-groups] dev via uv. It stays out of runtime dependencies.
- **Don't touch pyproject** — Only document pytest; you add it yourself.

---

## 5. Q&A

**Q1. Where should TROUBLESHOOTING, CONTRIBUTING, CHANGELOG, SECURITY and CODE_OF_CONDUCT live? (README stays at the day2/ root.)**

- ✅ **day2/ root (Recommended)** — GitHub convention: these files are found and shown automatically. docs/ holds the project and ML documentation.
- **day2/docs/** — Every markdown file in docs/, apart from README.

**Q2. Should the scaffold include a source package folder for the modular code?**

- ✅ **src/ folder with .gitkeep (Recommended)** — An empty src/ with .gitkeep, so modules have a home later. The package name is decided when code is written.
- **No source folder yet** — Decide the layout when code generation starts.

---

## 6. Prompt

```text
create a script named generate_tickets.py which generates the synthetic NetCore TAC tickets dataset. Use only NumPy and Pandas, and add NumPy's random value setting default for all randomness so the output is identical every run.

You already all columns with reference TAC dataset. If you need any support, refer docs\business use case text file.

Keep the following points to remember when you generate the dataset.

- Outliers (set resolution hours to 1500-3000 hours for about 1% of tickets, and set their resolution code to Hardware RMA
	and set their response in minutes to a negative value for 10 tickets)

- compute sla breached now, from the clean severity
- missing values
	a. about 5% of engineer experience in years and first response minutes
	b. 1% of severity set to NaN
- inconsistent values
	a. about 3% of severity values replaced with variants such as "SEV1", "Sev 1", "S1", "Sev-1"
	b. about 3% of region values with EMEA, emea, "amer ", " AMER "
- Near Duplicates
	a. copy about 2% of rows with a new ticket id
	b. few minutes later of created at timestamp
	c. channel switched between Email and Phone

the script should have reusable functions with appropriate docstring
the main function should have arguments passed for number of rows (--n), seed value (--seed) and output file (--output) by default it should be data\netcore_tickets.csv

Do you get all my requirements? If any questions, you can ask me, like I said in the system instructions.
```

---

## 7. Q&A

**Q1. Where should the generator code live, given the AGENTS.md rule of modular code in src/ and scripts in scripts/?**

- ✅ **src/ modules + thin script (Recommended)** — Reusable functions in src/netcore_tac/ (e.g. generator.py, quality_issues.py). scripts/generate_tickets.py only parses arguments and calls them. Easiest to unit test and reuse.
- **Single scripts/generate_tickets.py** — All functions and main() in one file under scripts/. Matches your wording literally, but it is closer to a monolithic script.

**Q2. Which tickets get the 10 negative first-response values?**

- ✅ **10 random tickets (Recommended)** — A separate data-entry-error issue, independent of the resolution-hour outliers. Two distinct data quality lessons.
- **10 of the outlier tickets** — Negative response only on rows that are already outliers (~1%). All the anomalies sit in the same rows.

**Q3. How should the ~2% near-duplicate rows affect the row count?**

- **Appended on top of --n (Recommended)** — --n 2000 gives about 2040 rows. New IDs continue the sequence (e.g. TKT-002001).
- ✅ **Included within --n** — Generate about 1960 originals plus about 40 duplicates, for exactly --n rows.

**Q4. Near duplicates switch channel between Email and Phone. What happens when the copied row's channel is Portal?**

- ✅ **Copy only Email/Phone rows (Recommended)** — Pick duplicate sources only from Email or Phone tickets, so every duplicate has a clean swap.
- **Portal stays Portal** — Any row can be copied; Portal duplicates keep the same channel.
- **Portal → random Email/Phone** — Any row can be copied; Portal becomes Email or Phone at random.

---

## 8. Q&A

**Q1. Having seen the comparison, keep near duplicates included within --n?**

- ✅ **Keep: within --n** — Exactly --n rows: about 98% originals plus about 2% duplicates.
- **Switch: appended** — --n unique tickets, plus about 2% duplicates on top.

**Q2. The inconsistent label examples only show S1/EMEA/AMER. How should they apply across all values?**

- ✅ **Apply to every level/region (Recommended)** — Severity: SEV{n}, Sev {n}, Sev-{n}, s{n} for S1–S4. Region: lowercase plus leading/trailing spaces for AMER, EMEA and APJC.
- **Exact examples only** — Only the listed strings (SEV1, Sev 1, Sev-1, EMEA, emea, 'amer ', ' AMER '), so only S1/EMEA/AMER rows get them.

**Q3. What should the column names look like?**

- ✅ **snake_case (Recommended)** — ticket_id, created_at, product_family, ..., resolution_hours. pandas-friendly, no quoting needed.
- **Title Case with spaces** — Ticket ID, Created At, ... Exactly as written in the business doc.

**Q4. What defaults should --n and --seed have?**

- ✅ **n=2000, seed=42 (Recommended)** — Matches the 2000+ tickets per year in the use case. 42 is the conventional seed.
- **n=5000, seed=42** — More rows for more stable models.
- **n=2500, seed=2025** — Slightly above 2000; the seed matches the 2025 data year.

---

## 9. Q&A

**Q1. How should Customer Comments be generated?**

- ✅ **~10 templates with {product} (Recommended)** — About 10 realistic templates, e.g. "BGP flaps on our {product} after upgrade", filled with the ticket's product family.
- **~10 comments per product family** — About 50 hand-written comments, 10 for each family. More realistic, but a longer script.

**Q2. When should SLA Breached be computed relative to the outliers?**

- ✅ **After outliers (Recommended)** — Order: generate clean data → outliers → SLA breached (from clean severity) → missing and inconsistent values → near duplicates. Outliers count as breached.
- **Before outliers** — SLA uses the original hours, so outliers can show 3000 hours with breached=False.

**Q3. Can the 1% NaN severity rows and the 3% severity-variant rows overlap?**

- ✅ **Disjoint rows (Recommended)** — Each dirty row has exactly one severity issue, so the counts match the stated percentages.
- **May overlap** — Pick rows independently; some variants get overwritten by NaN.

**Q4. After implementing, should I run the script to produce data/netcore_tickets.csv?**

- **Yes, generate the CSV (Recommended)** — Run once with defaults and report a short summary of rows and injected issues.
- ✅ **No, code and tests only** — You run it yourself in class.
