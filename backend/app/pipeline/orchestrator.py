import uuid
from app.schemas.pipeline_state import PipelineState, ValidationIssue
from app.pipeline.intent_extraction import intent_extractor
from app.pipeline.architecture_design import architecture_designer
from app.pipeline.schema_generation import schema_generator
from app.llm.client import LLMGenerationError


class PipelineOrchestrator:
    """Coordinates the multi-stage pipeline. Each stage reads/writes a single PipelineState."""

    def start(self, raw_prompt: str) -> PipelineState:
        state = PipelineState(
            request_id=str(uuid.uuid4()),
            raw_prompt=raw_prompt,
        )
        state = self.run_intent_stage(state)
        if state.status == "failed":
            return state

        state = self.run_architecture_stage(state)
        if state.status == "failed":
            return state

        state = self.run_schema_generation_stage(state)
        return state

    def run_intent_stage(self, state: PipelineState) -> PipelineState:
        try:
            intent = intent_extractor.extract(state.raw_prompt)
        except LLMGenerationError as e:
            state.status = "failed"
            state.validation_issues.append(
                ValidationIssue(layer="intent", severity="error", message=f"Intent extraction failed: {e}")
            )
            return state

        state.intent = intent
        state.status = "intent_done"

        for ambiguity in intent.ambiguities:
            state.validation_issues.append(
                ValidationIssue(layer="intent", severity="warning", message=ambiguity)
            )

        return state

    def run_architecture_stage(self, state: PipelineState) -> PipelineState:
        if state.intent is None:
            state.status = "failed"
            state.validation_issues.append(
                ValidationIssue(layer="architecture", severity="error", message="Cannot design architecture without intent")
            )
            return state

        try:
            architecture = architecture_designer.design(state.intent)
        except LLMGenerationError as e:
            state.status = "failed"
            state.validation_issues.append(
                ValidationIssue(layer="architecture", severity="error", message=f"Architecture design failed: {e}")
            )
            return state

        state.architecture = architecture
        state.status = "architecture_done"
        return state

    def run_schema_generation_stage(self, state: PipelineState) -> PipelineState:
        if state.architecture is None:
            state.status = "failed"
            state.validation_issues.append(
                ValidationIssue(layer="cross_layer", severity="error", message="Cannot generate schemas without architecture")
            )
            return state

        # Each layer is generated independently. If one fails, record it and continue
        # with the others rather than aborting the whole stage — this is what lets the
        # repair engine (next phase) target only the broken layer later.
        generators = {
            "ui": schema_generator.generate_ui,
            "api": schema_generator.generate_api,
            "db": schema_generator.generate_db,
            "auth": schema_generator.generate_auth,
            "business_logic": schema_generator.generate_business_logic,
        }

        any_failed = False
        for layer_name, generator_fn in generators.items():
            try:
                result = generator_fn(state.architecture)
                setattr(state, layer_name, result)
            except LLMGenerationError as e:
                any_failed = True
                state.validation_issues.append(
                    ValidationIssue(
                        layer=layer_name,
                        severity="error",
                        message=f"{layer_name} schema generation failed: {e}",
                    )
                )

        state.status = "failed" if any_failed else "schemas_done"
        return state


orchestrator = PipelineOrchestrator()