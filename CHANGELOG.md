# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added

- `docs/01-initial-setup-data-generation.md` — prompts and Q&A log for setup and data generation
- `notebooks/` folder (with `.gitkeep`) and its row in the `AGENTS.md` folder table
- `ipykernel` dev dependency for running notebooks in VS Code
- `notebooks/archive/ticket-resolution-ml-workflow-full.ipynb`: backup of the full detailed notebook (instructor reference)
- `.temp/notebook-lecture-notes.md`: instructor lecture notes, one entry per notebook cell tag (git-ignored)
- `notebooks/01-ticket-resolution-ml-workflow.ipynb`: title, business summary, learning objectives, setup, Part 0 (sections 1.1–1.9, including the first scikit-learn demo)
- Notebook Part 1 – Data Quality (sections 2.1–2.5): profiling, business metrics, label fixes, negative values, duplicates, mean vs median, IQR and outlier removal → `clean_df`
- Notebook Part 2 – Exploratory Data Analysis (sections 2.6–2.8): distribution and skew, severity/product/region/devices comparisons, correlation with leakage flagged, correlation vs cause, pivot tables, three insights
- Notebook Part 3 – Feature Engineering: feature lists and 80/20 split, one-hot encoding with an unseen product, scaling, `is_weekend` and `old_software` flags, leak-free preprocessing pipeline
- Notebook Part 4 – Linear Regression (sections 3.4, 3.5, 3.8): baseline, devices-only regression, full pipeline regression with driver ranking, MAE/RMSE/R² comparison, summary for support leadership

### Changed

- Notebook renamed to `notebooks/ticket-resolution-ml-workflow.ipynb` and slimmed for learners from escalation engineering: 251 → 85 cells, 16 sections in one running sequence, short notes only, one glossary, minimal EDA (1 section); simpler code (`duplicated()` for duplicates, flags added before the split, no `FunctionTransformer`); results unchanged (MAE 20.5 → 18.5 h)
- Every markdown cell tagged `[Cnn]`; code cells repeat the tag in their first comment
- `.gitignore`: `.temp/` (instructor-only files)
- Notebook review: ticket counts in the business summary and the 1.1/1.3 callouts now match the 5,000-ticket export; column-role table reduced to one line per role; y-axis labels added to both box plots; 3.3 pipeline cell split into two shorter cells

### Removed

- `notebooks/.gitkeep` (folder no longer empty)

## [0.2.0] - 2026-11-20

### Added

- `netcore_tac` package (`src/`): `config`, `generator`, `quality_issues`, `dataset`
- `scripts/generate_tickets.py` — CLI with `--n`, `--seed`, `--output`
- Synthetic NetCore TAC tickets with outliers, negative values, missing values, inconsistent labels and near duplicates
- Unit tests: `test_generator.py`, `test_quality_issues.py`, `test_dataset.py`

### Changed

- `pyproject.toml` — `uv_build` build backend so `netcore_tac` is importable
- Removed `.gitkeep` from `src/`, `scripts/`, `tests/` (no longer empty)

## [0.1.0] - 2026-11-20

### Added

- `AGENTS.md` — shared AI assistant rules
- `CLAUDE.md` and `.github/copilot-instructions.md` — pointers to `AGENTS.md`
- Standard files: `.gitignore`, `README.md`, `TROUBLESHOOTING.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `LICENSE` (MIT)
- Folder scaffold with `.gitkeep`: `src/`, `scripts/`, `tests/`, `data/`
- `pytest` as a dev dependency
