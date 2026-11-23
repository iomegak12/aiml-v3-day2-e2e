# Day 2 — TAC Desk Resolution-Time Prediction

ML training demonstration for **NetCore TAC Desk** (fictional networking vendor): predict ticket resolution hours at triage time.

- Business use case: [docs/business-use-case.txt](docs/business-use-case.txt)
- Session log (prompts + Q&A): [docs/01-initial-setup-data-generation.md](docs/01-initial-setup-data-generation.md)
- Lecture notes: `.temp/notebook-lecture-notes.md` (instructor-only, git-ignored); each entry matches a `[Cnn]` tag in the notebook
- Topics: Data Quality, EDA, Feature Engineering, Pipelines, Regression

## Project Structure

```
day2/
├── .github/
│   └── copilot-instructions.md   # Copilot pointer → AGENTS.md
├── data/                         # Sample / synthetic data
├── docs/                         # Project & ML documentation
├── notebooks/
│   ├── ticket-resolution-ml-workflow.ipynb      # Day 2 ML workflow (slim student version)
│   └── archive/
│       └── ticket-resolution-ml-workflow-full.ipynb   # Full detailed version (instructor reference)
├── scripts/
│   └── generate_tickets.py       # CLI: build synthetic dataset → CSV
├── src/
│   └── netcore_tac/
│       ├── config.py             # Probabilities, SLA hours, templates, issue settings
│       ├── generator.py          # Clean ticket generation
│       ├── quality_issues.py     # Outliers, missing, variants, near duplicates
│       └── dataset.py            # build_dataset(n, seed) pipeline
├── tests/                        # pytest unit tests
├── AGENTS.md                     # AI assistant rules (single source of truth)
├── CLAUDE.md                     # Claude Code pointer → AGENTS.md
├── pyproject.toml
└── README.md
```

## Setup

```bash
uv sync
```

## Generate the Dataset

```bash
uv run python scripts/generate_tickets.py                     # defaults below
uv run python scripts/generate_tickets.py --n 2000 --seed 42 --output data/netcore_tickets.csv
```

| Option | Default |
|--------|---------|
| `--n` | 2000 (near duplicates included) |
| `--seed` | 42 (same seed → identical output) |
| `--output` | `data/netcore_tickets.csv` |

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

## Run Tests

```bash
uv run pytest
```

## AI Assistant Rules

- Claude Code and GitHub Copilot both follow [AGENTS.md](AGENTS.md).

## Project Documents

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CHANGELOG.md](CHANGELOG.md)
- [SECURITY.md](SECURITY.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [LICENSE](LICENSE) — MIT
