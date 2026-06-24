import json
from app.llm.client import llm_client
from app.schemas.architecture import ArchitectureSchema
from app.schemas.ui_schema import UISchema
from app.schemas.api_schema import APISchema
from app.schemas.db_schema import DBSchema
from app.schemas.auth_schema import AuthSchema
from app.schemas.business_logic import BusinessLogicSchema
from app.pipeline.prompts import (
    UI_SCHEMA_SYSTEM_PROMPT,
    API_SCHEMA_SYSTEM_PROMPT,
    DB_SCHEMA_SYSTEM_PROMPT,
    AUTH_SCHEMA_SYSTEM_PROMPT,
    BUSINESS_LOGIC_SYSTEM_PROMPT,
)


class SchemaGenerator:
    """
    Stage 3 of the pipeline: turns ArchitectureSchema into UI, API, DB, Auth, and
    Business Logic schemas. Each layer is generated with its own dedicated LLM call
    (modular generation) rather than one combined prompt, so a later repair pass can
    regenerate a single broken layer without touching the others.
    """

    def _architecture_context(self, architecture: ArchitectureSchema) -> str:
        return (
            "Here is the application architecture to generate from:\n\n"
            f"ARCHITECTURE JSON:\n{json.dumps(architecture.model_dump(), indent=2)}"
        )

    def generate_ui(self, architecture: ArchitectureSchema) -> UISchema:
        return llm_client.generate_structured(
            system_prompt=UI_SCHEMA_SYSTEM_PROMPT,
            user_prompt=self._architecture_context(architecture),
            response_model=UISchema,
        )

    def generate_api(self, architecture: ArchitectureSchema) -> APISchema:
        return llm_client.generate_structured(
            system_prompt=API_SCHEMA_SYSTEM_PROMPT,
            user_prompt=self._architecture_context(architecture),
            response_model=APISchema,
        )

    def generate_db(self, architecture: ArchitectureSchema) -> DBSchema:
        return llm_client.generate_structured(
            system_prompt=DB_SCHEMA_SYSTEM_PROMPT,
            user_prompt=self._architecture_context(architecture),
            response_model=DBSchema,
        )

    def generate_auth(self, architecture: ArchitectureSchema) -> AuthSchema:
        return llm_client.generate_structured(
            system_prompt=AUTH_SCHEMA_SYSTEM_PROMPT,
            user_prompt=self._architecture_context(architecture),
            response_model=AuthSchema,
        )

    def generate_business_logic(self, architecture: ArchitectureSchema) -> BusinessLogicSchema:
        return llm_client.generate_structured(
            system_prompt=BUSINESS_LOGIC_SYSTEM_PROMPT,
            user_prompt=self._architecture_context(architecture),
            response_model=BusinessLogicSchema,
        )


schema_generator = SchemaGenerator()