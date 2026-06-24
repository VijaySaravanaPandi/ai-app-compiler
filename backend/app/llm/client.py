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
            "- Respond with ONLY a valid JSON instance/object representing the actual data. Do NOT include markdown fences, preamble, or explanations.\n"
            "- Do NOT output the schema structure itself (i.e. do NOT output '$defs', 'properties', 'required', 'additionalProperties', 'description', or 'type' at the root level).\n"
            "- The JSON output must be a single concrete object that matches the fields defined in the schema below:\n"
            f"{json.dumps(response_model.model_json_schema(), indent=2)}\n"
        )

        import time
        import openai

        max_attempts = 5
        backoff_sec = 2.0
        response = None

        for attempt in range(1, max_attempts + 1):
            try:
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
                break
            except openai.RateLimitError as e:
                if attempt == max_attempts:
                    raise LLMGenerationError(f"Rate limit exceeded after {max_attempts} attempts: {e}")
                # Parse retry-after from error message if possible
                sleep_time = backoff_sec
                match = re.search(r"try again in ([\d\.]+)s", str(e))
                if match:
                    sleep_time = float(match.group(1)) + 1.0
                else:
                    sleep_time = backoff_sec * (2 ** (attempt - 1))
                print(f"[LLMClient] Rate limit hit. Retrying in {sleep_time:.2f}s... (Attempt {attempt}/{max_attempts})")
                time.sleep(sleep_time)
            except openai.OpenAIError as e:
                if attempt == max_attempts:
                    raise LLMGenerationError(f"OpenAI error: {e}")
                sleep_time = backoff_sec * (2 ** (attempt - 1))
                print(f"[LLMClient] OpenAI error. Retrying in {sleep_time:.2f}s... (Attempt {attempt}/{max_attempts})")
                time.sleep(sleep_time)

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