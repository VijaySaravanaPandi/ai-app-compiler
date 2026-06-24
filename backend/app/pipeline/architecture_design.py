import json
from app.llm.client import llm_client
from app.schemas.intent import IntentSchema
from app.schemas.architecture import ArchitectureSchema
from app.pipeline.prompts import ARCHITECTURE_DESIGN_SYSTEM_PROMPT


class ArchitectureDesigner:
    """Stage 2 of the pipeline: turns IntentSchema into ArchitectureSchema."""

    def design(self, intent: IntentSchema) -> ArchitectureSchema:
        user_prompt = (
            "Here is the structured intent extracted from the user's request. "
            "Design the application architecture from it.\n\n"
            f"INTENT JSON:\n{json.dumps(intent.model_dump(), indent=2)}"
        )

        return llm_client.generate_structured(
            system_prompt=ARCHITECTURE_DESIGN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ArchitectureSchema,
        )


architecture_designer = ArchitectureDesigner()