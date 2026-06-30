from typing import List

from core.features.ingestion.pipeline.models import LLMExtractionReturnType
from core.features.ingestion.pipeline.tracker import run_step
from core.openai import groq

PROMPT_PATH = "core/features/ingestion/pipeline/extraction_prompt.txt"


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


def _load_prompt() -> str:
    with open(PROMPT_PATH) as f:
        return f.read()


async def extract_with_llm(images_b64: List[str]) -> LLMExtractionReturnType:
    content = _build_image_content(images_b64)
    system_prompt = _load_prompt()

    try:
        response = groq.beta.chat.completions.parse(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},  # type:ignore
            ],
            response_format=LLMExtractionReturnType,
        )
    except Exception as e:
        if "json_validate_failed" in str(e):
            raise Exception(
                "LLM output failed schema validation. Check model types/quantities."
            )
        raise e

    parsed = response.choices[0].message.parsed
    if parsed is None:
        refusal = getattr(response.choices[0].message, "refusal", None)
        raise Exception(f"Failed to structure extracted text. Refusal: {refusal}")

    return parsed


async def run_extraction_phase(ctx, tracker, publish):
    phase = "extracting_data"
    await publish(phase, "in_progress")

    ctx["structured_data"] = await run_step(
        tracker, phase, "extract_with_llm", extract_with_llm, ctx["images_b64"]
    )

    await publish(phase, "completed")
