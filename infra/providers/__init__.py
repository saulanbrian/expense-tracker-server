import logging
from typing import TypeVar

from pydantic import BaseModel

from infra.providers.gemini import _call_gemini
from infra.providers.models import ModelConfig
from infra.providers.openrouter import _call_openrouter

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


TEXT_FALLBACK_CHAIN = [
    ModelConfig("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "openrouter"),
    ModelConfig("dots-studio/dots-3-note-preview:free", "openrouter"),
    ModelConfig("gemini-3.6-flash", "gemini"),
]

VISION_FALLBACK_CHAIN = [
    ModelConfig("nvidia/nemotron-nano-12b-v2-vl:free", "openrouter"),
    ModelConfig("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "openrouter"),
    ModelConfig("gemini-3.6-flash", "gemini"),
]


def call_llm(
    response_format: type[T],
    messages: list,
    chain: list[ModelConfig] | None = None,
) -> T:
    model_list = chain or TEXT_FALLBACK_CHAIN
    last_error: Exception | None = None

    for config in model_list:
        try:
            if config.provider == "gemini":
                return _call_gemini(config, messages, response_format)
            return _call_openrouter(config, messages, response_format)
        except Exception as e:
            logger.warning(f"Model {config.model} ({config.provider}) failed: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All models failed. Last error: {last_error}")
