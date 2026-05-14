"""
Local audit runner for NexusAI repository.

Usage: python run_audit.py

This script attempts to execute pytest, flake8, bandit and prints useful hints
when tools are not available. Run inside your virtual environment where
backend/requirements-dev.txt has been installed.
"""

import subprocess
import shutil
import sys

CHECKS = [
    ("Pytest", [sys.executable, "-m", "pytest", "-q"]),
    ("Flake8", ["flake8"]),
    ("Bandit", ["bandit", "-r", ".", "-f", "txt"]),
]


def run_check(name, cmd):
    print(f"=== {name} ===")
    try:
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            print(f"{name} exited with code {proc.returncode}")
    except FileNotFoundError:
        print(f"{name} not found. Install dev deps: pip install -r backend/requirements-dev.txt")


if __name__ == "__main__":
    for name, cmd in CHECKS:
        run_check(name, cmd)

    print("\nAudit finished. To enable CI, copy CI_WORKFLOW_TEMPLATE.yml to .github/workflows/ci.yml")
