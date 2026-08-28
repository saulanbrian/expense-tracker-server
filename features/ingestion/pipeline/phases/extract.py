from openai.types.chat import ChatCompletionMessageParam

from domain.schemas import LLMExtractionReturnType, PipelineContext
from infra.providers import TEXT_FALLBACK_CHAIN, VISION_FALLBACK_CHAIN, call_llm

EXTRACTION_PROMPT_PATH = "features/ingestion/pipeline/extraction_prompt.txt"
TEXT_EXTRACTION_PROMPT_PATH = "features/ingestion/pipeline/text_extraction_prompt.txt"


def _load_prompt(path: str) -> str:
    with open(path) as f:
        return f.read()


def _build_image_content(images_b64: list[str]) -> list[dict]:
    content: list[dict] = []
    for i, img in enumerate(images_b64):
        content.append({"type": "text", "text": f"Page {i + 1}:"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"},
            }
        )
    return content


def _build_text_content(extracted_text: str | list[str]) -> str:
    if isinstance(extracted_text, list):
        return "\n".join(extracted_text)
    return extracted_text


async def _extract_with_text(extracted_text: str | list[str]) -> LLMExtractionReturnType:
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


async def _extract_with_vision(images_b64: list[str]) -> LLMExtractionReturnType:
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


async def run_extract(ctx: PipelineContext, update_status) -> None:
    phase = "extracting_data"
    await update_status(phase, "in_progress")

    if ctx.extracted_text:
        result = await _extract_with_text(ctx.extracted_text)
        if not result.needs_vision:
            ctx.structured_data = result
            await update_status(phase, "completed")
            return

    ctx.structured_data = await _extract_with_vision(ctx.images_b64)

    await update_status(phase, "completed")
