import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0"))
    MAX_REPAIR_ATTEMPTS: int = int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
    GENERATED_APPS_DIR: Path = Path(os.getenv("GENERATED_APPS_DIR", "./generated_apps"))

    def validate(self):
        if not self.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        self.GENERATED_APPS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()