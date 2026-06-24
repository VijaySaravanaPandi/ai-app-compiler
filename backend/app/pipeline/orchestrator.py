import uuid
from app.schemas.pipeline_state import PipelineState, ValidationIssue
from app.pipeline.intent_extraction import intent_extractor
from app.llm.client import LLMGenerationError


class PipelineOrchestrator:
    """Coordinates the multi-stage pipeline. Each stage reads/writes a single PipelineState."""

    def start(self, raw_prompt: str) -> PipelineState:
        state = PipelineState(
            request_id=str(uuid.uuid4()),
            raw_prompt=raw_prompt,
        )
        return self.run_intent_stage(state)

    def run_intent_stage(self, state: PipelineState) -> PipelineState:
        try:
            intent = intent_extractor.extract(state.raw_prompt)
        except LLMGenerationError as e:
            state.status = "failed"
            state.validation_issues.append(
                ValidationIssue(
                    layer="intent",
                    severity="error",
                    message=f"Intent extraction failed: {e}",
                )
            )
            return state

        state.intent = intent
        state.status = "intent_done"

        for ambiguity in intent.ambiguities:
            state.validation_issues.append(
                ValidationIssue(
                    layer="intent",
                    severity="warning",
                    message=ambiguity,
                )
            )

        return state


orchestrator = PipelineOrchestrator()