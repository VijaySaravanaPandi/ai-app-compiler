from app.llm.client import llm_client
from app.schemas.intent import IntentSchema
from app.pipeline.prompts import INTENT_EXTRACTION_SYSTEM_PROMPT


class IntentExtractor:
    """Stage 1 of the pipeline: turns a raw natural-language prompt into a structured IntentSchema."""

    def extract(self, raw_prompt: str) -> IntentSchema:
        result = llm_client.generate_structured(
            system_prompt=INTENT_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=raw_prompt,
            response_model=IntentSchema,
        )

        # Defensive override: guarantee raw_input is always exactly what the
        # user typed, regardless of what the model produced.
        result.raw_input = raw_prompt

        return result


intent_extractor = IntentExtractor()