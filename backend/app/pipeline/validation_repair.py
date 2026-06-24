import json
from typing import List

from app.schemas.pipeline_state import PipelineState, ValidationIssue, RepairLogEntry
from app.llm.client import LLMClient, LLMGenerationError
from datetime import datetime

class ValidationRepairEngine:
    """Phase 6: Detect remaining validation issues and attempt repairs.

    The engine walks through ``state.validation_issues`` produced by the
    ``RefinementEngine``.  For each issue it tries a deterministic auto‑repair
    first (already applied by the refinement stage).  If the issue remains, we
    fall back to an LLM‑driven repair that asks the model for a corrected slice
    of the offending schema.

    The approach is intentionally lightweight – it does **not** attempt a full
    regeneration of the entire pipeline, which would be costly and nondetermin‑
    istic.  Instead we target the minimal layer required (e.g. ``api`` or ``db``)
    and replace the specific object we know is broken.

    On success a ``RepairLogEntry`` is appended to ``state.repair_log`` and the
    issue is removed from ``state.validation_issues``.  Errors that cannot be
    repaired keep the pipeline in the ``failed`` state so the caller can expose
    a helpful error to the user.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()

    def run(self, state: PipelineState) -> PipelineState:
        """Process all validation issues and attempt repairs.

        Returns the mutated ``state``.  ``state.status`` will be ``"failed"`` if
        any *error*‑severity issue remains unrepaired; otherwise it becomes
        ``"validated"``.
        """
        if not state.validation_issues:
            state.status = "validated"
            return state

        # Work on a copy to avoid mutating while iterating
        remaining_issues: List[ValidationIssue] = []
        for issue in state.validation_issues:
            try:
                repaired = self._attempt_repair(state, issue)
                if not repaired:
                    remaining_issues.append(issue)
            except Exception as exc:  # pragma: no cover – defensive
                # If something unexpected happens we keep the issue and log it
                remaining_issues.append(issue)
                state.repair_log.append(
                    RepairLogEntry(
                        timestamp=datetime.utcnow().isoformat(),
                        layer=issue.layer,
                        issue=f"Exception during repair: {exc}",
                        action="failed",
                        attempt=1,
                    )
                )

        state.validation_issues = remaining_issues
        # Determine final status
        has_error = any(i.severity == "error" for i in remaining_issues)
        state.status = "failed" if has_error else "validated"
        return state

    def _attempt_repair(self, state: PipelineState, issue: ValidationIssue) -> bool:
        """Try to repair a single issue.

        Returns ``True`` when the issue was fixed and removed from the state.
        """
        # Only attempt LLM repair for error‑level issues – warnings are optional
        if issue.severity not in {"error", "warning"}:
            return False

        # Build a minimal prompt that includes the architecture, the problematic
        # layer and the exact issue description.
        prompt = (
            f"You are a deterministic schema repair assistant. The user supplied\n"
            f"a high‑level architecture and generated schemas. The following\n"
            f"validation issue was detected in layer '{issue.layer}':\n"
            f"{issue.message}\n"
            f"Please output a **valid JSON** snippet that fixes the problem.\n"
            f"Only return the JSON for the affected layer (e.g. full API schema,\n"
            f"or the specific endpoint object). Do not add any extra commentary."
        )

        # Determine which attribute of ``state`` corresponds to the layer name.
        layer_obj = getattr(state, issue.layer, None)
        if layer_obj is None:
            # Unknown layer – cannot repair automatically.
            return False

        # Call the LLM client – we rely on its built‑in retry / back‑off.
        try:
            response = self.llm_client.generate(prompt)
        except LLMGenerationError:
            # If LLM fails we treat it as unrepaired.
            return False

        # The LLM is expected to return JSON.  We attempt to parse it.
        try:
            repaired_obj = json.loads(response)
        except json.JSONDecodeError:
            # Invalid JSON – cannot apply repair.
            return False

        # Replace the problematic layer with the repaired version.
        setattr(state, issue.layer, repaired_obj)
        # Log the successful repair.
        state.repair_log.append(
            RepairLogEntry(
                timestamp=datetime.utcnow().isoformat(),
                layer=issue.layer,
                issue=issue.message,
                action="repaired",
                attempt=1,
            )
        )
        return True
