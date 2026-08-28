from dataclasses import dataclass


@dataclass
class ModelConfig:
    model: str
    provider: str  # "openrouter" or "gemini"
