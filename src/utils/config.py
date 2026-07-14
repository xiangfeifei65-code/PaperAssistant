import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    API_KEY: str
    MODEL: str
    BASE_URL: str
    MAX_RETRIES: int
    RETRY_DELAY: int
    DEFAULT_MAX_RESULTS: int

    @classmethod
    def from_env(cls):
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            raise ValueError("LLM_API_KEY not set")
        return cls(
            API_KEY=api_key,
            MODEL=os.getenv("LLM_MODEL_ID", "gpt-3.5-turbo"),
            BASE_URL=os.getenv("LLM_BASE_URL", ""),
            MAX_RETRIES=int(os.getenv("MAX_RETRIES", "3")),
            RETRY_DELAY=int(os.getenv("RETRY_DELAY", "2")),
            DEFAULT_MAX_RESULTS=int(os.getenv("DEFAULT_MAX_RESULTS", "5")),
        )

# 全局配置实例
config = Config.from_env()