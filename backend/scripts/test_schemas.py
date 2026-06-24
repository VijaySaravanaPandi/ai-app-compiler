"""
Quick manual test for Stage 1 + 2 + 3 — full schema generation pipeline.
Run from the backend/ folder with the venv active:
    python scripts/test_schemas.py
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
        print("\n--- UI ---")
        print(json.dumps(state.ui.model_dump() if state.ui else None, indent=2))
        print("\n--- API ---")
        print(json.dumps(state.api.model_dump() if state.api else None, indent=2))
        print("\n--- DB ---")
        print(json.dumps(state.db.model_dump() if state.db else None, indent=2))
        print("\n--- AUTH ---")
        print(json.dumps(state.auth.model_dump() if state.auth else None, indent=2))
        print("\n--- BUSINESS LOGIC ---")
        print(json.dumps(state.business_logic.model_dump() if state.business_logic else None, indent=2))

        if state.validation_issues:
            print("\n--- VALIDATION ISSUES ---")
            for issue in state.validation_issues:
                print(f"[{issue.severity}] {issue.layer}: {issue.message}")