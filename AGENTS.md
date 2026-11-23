# AI Assistant Instructions

> Single source of truth for **Claude Code** (via `CLAUDE.md`) and **GitHub Copilot** (via `.github/copilot-instructions.md`).
> Scope: this `day2/` project only.

## 1. Interaction Rules

- **No assumptions** — if anything is unclear, ask before acting.
- **No content unless asked** — do not generate scripts, commands, files or code until explicitly requested.
- **Brief by default** — bulleted points, list of items, titles only. Give detail only when asked.
- **Questions as MCQs** — every clarifying question is multiple choice, never prose.
- **Non-obvious choices** — when the user selects an unusual / non-recommended option, show:
  - the available options
  - pros / cons of each
  - why the selected option should NOT be chosen

## 2. Code Rules

- **Modular code** — small, single-purpose modules under `src/`; no monolithic scripts.
- **Reusable scripts** — under `scripts/`.

## 3. Folder Conventions

| Folder     | Purpose                                         |
|------------|-------------------------------------------------|
| `src/`     | Modular source code                             |
| `scripts/` | Reusable scripts                                |
| `tests/`   | Unit tests                                      |
| `data/`    | All data — sample, synthetic or generated       |
| `docs/`    | Project and ML documentation                    |
| `notebooks/` | Jupyter notebooks                             |

- Keep a `.gitkeep` in every folder that would otherwise be empty.

## 4. Testing Rules

- **Unit tests are mandatory** — every module must have pytest unit tests in `tests/` proving it works.
- **No other test types by default** — no integration, web, end-to-end or other testing unless explicitly asked.
- Run tests with: `uv run pytest`

## 5. Standard Project Files

Must exist and be kept current:

- `.gitignore`
- `README.md`
- `TROUBLESHOOTING.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `LICENSE` (MIT)

## 6. Documentation Upkeep

- **Update `README.md`** whenever any development takes place (new modules, scripts, data, docs, commands).
- **Add a `CHANGELOG.md` entry** for every change.
- Update `TROUBLESHOOTING.md` when a new issue and its fix are found.
