import base64
import json
from typing import Any, TypeVar

from google.genai import types
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ValidationError

from infra.llm import gemini_client
from infra.providers.models import ModelConfig
from infra.providers.utils import _strip_markdown_json

T = TypeVar("T", bound=BaseModel)


def _map_role(role: str) -> str:
    return "user" if role == "user" else "model"


def _decode_image(url: str) -> types.Part:
    if "," not in url:
        return types.Part.from_text(text=url)
    b64_data = url.split(",", 1)[1]
    image_bytes = base64.b64decode(b64_data)
    mime = "image/jpeg"
    if url.startswith("data:"):
        mime = url.split(";")[0].split(":")[1]
    return types.Part.from_bytes(data=image_bytes, mime_type=mime)


def _build_parts(content: Any) -> list[types.Part]:
    if isinstance(content, str):
        return [types.Part.from_text(text=content)]
    if not isinstance(content, list):
        return [types.Part.from_text(text=str(content))]
    parts = []
    for item in content:
        if not isinstance(item, dict):
            parts.append(types.Part.from_text(text=str(item)))
        elif item.get("type") == "text":
            parts.append(types.Part.from_text(text=item.get("text", "")))
        elif item.get("type") == "image_url":
            parts.append(_decode_image(item.get("image_url", {}).get("url", "")))
        else:
            parts.append(types.Part.from_text(text=str(item)))
    return parts


def _build_contents(
    messages: list[ChatCompletionMessageParam],
):
    system_instruction = None
    contents = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            system_instruction = content if isinstance(content, str) else str(content)
            continue

        parts = _build_parts(content)
        contents.append(types.Content(role=_map_role(role), parts=parts))

    return contents, system_instruction


def _parse_response(raw_content: str, response_format: type[T]) -> T:
    cleaned = _strip_markdown_json(raw_content)
    try:
        return response_format.model_validate_json(cleaned)
    except ValidationError:
        return response_format.model_validate(json.loads(cleaned))


def _call_gemini(
    config: ModelConfig,
    messages: list[ChatCompletionMessageParam],
    response_format: type[T],
) -> T:
    if gemini_client is None:
        raise RuntimeError("Gemini client not configured (missing GEMINI_API_KEY)")

    contents, system_instruction = _build_contents(messages)

    gen_config = types.GenerateContentConfig(response_mime_type="application/json")
    if system_instruction:
        gen_config.system_instruction = system_instruction

    response = gemini_client.models.generate_content(
        model=config.model,
        contents=contents,
        config=gen_config,
    )

    if response.text is None:
        raise RuntimeError("Gemini returned empty content")

    return _parse_response(response.text, response_format)
