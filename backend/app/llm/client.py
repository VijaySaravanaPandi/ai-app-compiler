import json
import re
from typing import Type, TypeVar
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMGenerationError(Exception):
    """Raised when the LLM output cannot be parsed/validated, even after stripping fences."""
    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


class LLMClient:
    def __init__(self):
        settings.validate()
        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
        )
        self.model = settings.MODEL_NAME

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
        return text

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = None,
        max_tokens: int = 4096,
    ) -> T:
        temp = settings.TEMPERATURE if temperature is None else temperature

        full_system = (
            f"{system_prompt}\n\n"
            "CRITICAL OUTPUT RULES:\n"
            "- Respond with ONLY valid JSON. No markdown fences, no preamble, no explanation.\n"
            "- The JSON MUST conform exactly to this schema (extra fields are forbidden):\n"
            f"{json.dumps(response_model.model_json_schema(), indent=2)}\n"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temp,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw_text = response.choices[0].message.content or ""
        cleaned = self._strip_code_fences(raw_text)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMGenerationError(f"Invalid JSON from model: {e}", raw_output=raw_text)

        try:
            return response_model.model_validate(data)
        except ValidationError as e:
            raise LLMGenerationError(f"Schema validation failed: {e}", raw_output=raw_text)


llm_client = LLMClient()