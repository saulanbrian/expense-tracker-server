import json
from typing import TypeVar

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

from infra.llm import openrouter_client
from infra.providers.models import ModelConfig
from infra.providers.utils import _strip_markdown_json

T = TypeVar("T", bound=BaseModel)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code >= 500
    return False


def _call_openrouter(
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
        response = openrouter_client.chat.completions.create(
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
