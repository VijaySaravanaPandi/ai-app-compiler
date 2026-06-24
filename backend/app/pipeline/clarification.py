"""
Clarification Engine — pre-pipeline guard
=========================================
Checks if a raw prompt is too vague or underspecified to produce a
meaningful app.  If it is, it sets ``state.needs_clarification = True``
and populates ``state.clarification_questions`` instead of proceeding.

A prompt is considered "too vague" when it meets any of the following:
  * Fewer than 8 words total
  * No entity/domain noun detected (no concrete nouns beyond stop words)
  * Contradictory roles (e.g. both "no admin" and "admin" in the same prompt)

When the prompt is borderline (e.g. 1-2 entities, no features listed) the
engine makes reasonable assumptions and documents them instead of blocking.
"""

from __future__ import annotations

import re
from typing import List

from app.schemas.pipeline_state import PipelineState, ValidationIssue

# Very simple keyword-based heuristics — no LLM call, fully deterministic.
_ENTITY_KEYWORDS = re.compile(
    r"\b(user|contact|product|order|post|comment|event|task|project|invoice|"
    r"payment|subscription|plan|report|ticket|customer|employee|role|team|"
    r"category|tag|message|notification|dashboard|analytic)\b",
    re.IGNORECASE,
)

_CONTRADICTION_PAIRS = [
    (r"\bno admin\b", r"\badmin\b"),
    (r"\bno login\b", r"\blogin\b"),
    (r"\bpublic\b.*\bprivate\b", None),   # conflicting access model
]

_MIN_WORD_COUNT = 5


def _word_count(text: str) -> int:
    return len(text.split())


def _find_contradictions(text: str) -> List[str]:
    issues = []
    lower = text.lower()
    for pattern_a, pattern_b in _CONTRADICTION_PAIRS:
        if pattern_b is None:
            if re.search(pattern_a, lower):
                issues.append(f"Contradictory access model detected: '{pattern_a}'")
        else:
            if re.search(pattern_a, lower) and re.search(pattern_b, lower):
                issues.append(
                    f"Conflicting requirements: '{pattern_a}' and '{pattern_b}' in the same prompt."
                )
    return issues


class ClarificationEngine:
    """
    Lightweight, deterministic clarification detector.
    Called before the Intent Extraction LLM stage to avoid wasting tokens on
    unparseable inputs.
    """

    def check(self, state: PipelineState) -> PipelineState:
        prompt = state.raw_prompt.strip()
        questions: List[str] = []

        # 1. Too short
        if _word_count(prompt) < _MIN_WORD_COUNT:
            questions.append(
                "Your prompt is very short. What type of application do you want to build? "
                "Please describe its main features, users, and any special requirements."
            )

        # 2. No recognisable entity keywords
        if not _ENTITY_KEYWORDS.search(prompt):
            questions.append(
                "We couldn't identify any concrete data entities (e.g. users, products, orders). "
                "What are the main things your app needs to store or manage?"
            )

        # 3. Contradictions
        for contradiction in _find_contradictions(prompt):
            state.validation_issues.append(
                ValidationIssue(layer="intent", severity="warning", message=contradiction)
            )
            questions.append(
                f"We detected a conflicting requirement: {contradiction} — "
                "Could you clarify what you meant?"
            )

        if questions:
            state.needs_clarification = True
            state.clarification_questions = questions
            state.status = "needs_clarification"

        return state


clarification_engine = ClarificationEngine()
