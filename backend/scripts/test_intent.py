"""
Quick manual test for Stage 1 — Intent Extraction.
Run from the backend/ folder with the venv active:
    python scripts/test_intent.py
"""
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.pipeline.orchestrator import orchestrator

TEST_PROMPTS = [
    "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
    "I want an app",
    "Build a blog where anyone can post anything and also delete other people's posts as admin but also no admin role",
]

if __name__ == "__main__":
    for prompt in TEST_PROMPTS:
        print("=" * 80)
        print("PROMPT:", prompt)
        state = orchestrator.start(prompt)
        print(json.dumps(state.model_dump(), indent=2))