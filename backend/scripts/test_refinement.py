"""
Quick manual test for the full pipeline through Stage 4 — Refinement.
Run from the backend/ folder with the venv active:
    python scripts/test_refinement.py
"""
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.pipeline.orchestrator import orchestrator

TEST_PROMPTS = [
    "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
]

if __name__ == "__main__":
    for prompt in TEST_PROMPTS:
        print("=" * 80)
        print("PROMPT:", prompt)
        state = orchestrator.start(prompt)

        print("STATUS:", state.status)

        print("\n--- VALIDATION ISSUES (cross-layer checks) ---")
        if not state.validation_issues:
            print("None found.")
        for issue in state.validation_issues:
            print(f"[{issue.severity}] {issue.layer}: {issue.message}")

        print("\n--- REPAIR LOG (automatic fixes applied) ---")
        if not state.repair_log:
            print("None applied.")
        for entry in state.repair_log:
            print(f"[{entry.action}] {entry.layer}: {entry.issue}")