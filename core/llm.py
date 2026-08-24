import json
import logging
from dataclasses import dataclass
from typing import TypeVar

from google.genai import types
from openai import RateLimitError
from openai._exceptions import APIStatusError
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from core.openai import client, gemini_client

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseModel")


@dataclass
class ModelConfig:
    model: str
    provider: str  # "openrouter" or "gemini"


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


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code >= 500
    return False


def _strip_markdown_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def _call_gemini(
    config: ModelConfig,
    messages: list[ChatCompletionMessageParam],
    response_format: type[T],
) -> T:
    if gemini_client is None:
        raise RuntimeError("Gemini client not configured (missing GEMINI_API_KEY)")

    system_instruction = None
    contents = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        text = content if isinstance(content, str) else str(content)

        if role == "system":
            system_instruction = text
        else:
            contents.append(types.Content(
                role="user" if role == "user" else "model",
                parts=[types.Part.from_text(text=text)]
            ))

    gen_config = types.GenerateContentConfig(
        response_mime_type="application/json",
    )
    if system_instruction:
        gen_config.system_instruction = system_instruction

    response = gemini_client.models.generate_content(
        model=config.model,
        contents=contents,
        config=gen_config,
    )

    raw_content = response.text
    if raw_content is None:
        raise RuntimeError("Gemini returned empty content")

    cleaned = _strip_markdown_json(raw_content)
    try:
        return response_format.model_validate_json(cleaned)
    except ValidationError:
        parsed = json.loads(cleaned)
        return response_format.model_validate(parsed)


def call_llm(
    response_format: type[T],
    messages: list[ChatCompletionMessageParam],
    chain: list[ModelConfig] | None = None,
) -> T:
    model_list = chain or TEXT_FALLBACK_CHAIN
    last_error: Exception | None = None

    for config in model_list:
        try:
            if config.provider == "gemini":
                return _call_gemini(config, messages, response_format)
            return _call_with_retry(config, messages, response_format)
        except Exception as e:
            logger.warning(f"Model {config.model} ({config.provider}) failed: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All models failed. Last error: {last_error}")


def _call_with_retry(
    config: ModelConfig,
    messages: list[ChatCompletionMessageParam],
    response_format: type[T],
) -> T:
    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _do_call() -> T:
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        if raw_content is None:
            raise RuntimeError("Model returned empty content")

        cleaned = _strip_markdown_json(raw_content)
        try:
            return response_format.model_validate_json(cleaned)
        except ValidationError:
            parsed = json.loads(cleaned)
            return response_format.model_validate(parsed)

    return _do_call()
