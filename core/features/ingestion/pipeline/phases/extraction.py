from typing import List

from openai.types.chat import ChatCompletionMessageParam

from core.features.ingestion.pipeline.models import LLMExtractionReturnType
from core.llm import TEXT_FALLBACK_CHAIN, VISION_FALLBACK_CHAIN, call_llm

EXTRACTION_PROMPT_PATH = "core/features/ingestion/pipeline/extraction_prompt.txt"
TEXT_EXTRACTION_PROMPT_PATH = "core/features/ingestion/pipeline/text_extraction_prompt.txt"


def _load_prompt(path: str) -> str:
    with open(path) as f:
        return f.read()


def _build_image_content(images_b64: List[str]) -> List[dict]:
    content: List[dict] = []
    for i, img in enumerate(images_b64):
        content.append({"type": "text", "text": f"Page {i + 1}:"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"},
            }
        )
    return content


def _build_text_content(extracted_text: str) -> str:
    return extracted_text


async def extract_with_text_llm(extracted_text: str) -> LLMExtractionReturnType:
    system_prompt = _load_prompt(TEXT_EXTRACTION_PROMPT_PATH)
    text_content = _build_text_content(extracted_text)

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text_content},
    ]

    return call_llm(
        response_format=LLMExtractionReturnType,
        messages=messages,
        chain=TEXT_FALLBACK_CHAIN,
    )


async def extract_with_vision_llm(images_b64: List[str]) -> LLMExtractionReturnType:
    content = _build_image_content(images_b64)
    system_prompt = _load_prompt(EXTRACTION_PROMPT_PATH)

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},  # type:ignore
    ]

    return call_llm(
        response_format=LLMExtractionReturnType,
        messages=messages,
        chain=VISION_FALLBACK_CHAIN,
    )


async def run_extraction_phase(ctx, update_status):
    phase = "extracting_data"
    await update_status(phase, "in_progress")

    extracted_text = ctx.get("extracted_text", "")
    images_b64 = ctx["images_b64"]

    if extracted_text:
        result = await extract_with_text_llm(extracted_text)
        if not result.needs_vision:
            ctx["structured_data"] = result
            await update_status(phase, "completed")
            return
        ctx["extraction_reason"] = result.reason

    ctx["structured_data"] = await extract_with_vision_llm(images_b64)

    await update_status(phase, "completed")
