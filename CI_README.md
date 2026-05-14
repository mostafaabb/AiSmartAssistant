CI & Local Audit
=================

This repo includes a CI workflow template and a small local audit script to help reach a "0 issues" state.

Files added:
- CI_WORKFLOW_TEMPLATE.yml  — GitHub Actions workflow template. Copy this file to `.github/workflows/ci.yml` to enable CI.
- run_audit.py              — Simple local script to run pytest, flake8, and bandit. Run with `python run_audit.py` inside your venv.

How to enable CI (manual steps):
1. Copy `CI_WORKFLOW_TEMPLATE.yml` into `.github/workflows/ci.yml` (create `.github/workflows` directories if missing).
2. Ensure `backend/requirements-dev.txt` contains dev deps (flake8, bandit, pytest).
3. Push to GitHub — Actions will run on push/PR.

Notes & next steps:
- The environment used by this assistant lacks PowerShell Core, so I created local artifacts instead. If you want, I can prepare a PR with these files and CI enabled (requires repository push access).
- After CI is enabled, run the workflow and share any failing logs; I will fix failures and open PRs with changes that make tests/lints pass.
