# Copilot Instructions

Follow all rules in [AGENTS.md](../AGENTS.md) — it is the single source of truth.

Key rules (summary only; `AGENTS.md` wins on any conflict):

- No assumptions — clarify first
- No content (scripts, commands, files, code) unless asked
- Brief by default — bullets, titles only
- Questions as MCQs only
- Non-obvious choice → show options, pros/cons, why NOT
- Modular code in `src/`; scripts in `scripts/`; data in `data/`; docs in `docs/`
- Mandatory pytest unit tests in `tests/`; no other test types unless asked
- Update `README.md` and `CHANGELOG.md` on every change
