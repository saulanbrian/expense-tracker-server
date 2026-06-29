import base64
import io
from typing import List

import httpx
from dotenv import load_dotenv
from pdf2image import convert_from_bytes

from core.openai import groq

from .models import LLMExtractionReturnType

load_dotenv(override=True)

FRANKFURTER_API = "https://api.frankfurter.dev"


def _get_usd_rate(currency: str, billing_date: str) -> float:
    currency = currency.upper().strip()
    if currency == "USD":
        return 1.0

    url = f"{FRANKFURTER_API}/v2/rate/{currency}/USD"
    params = {"date": billing_date}

    with httpx.Client(timeout=10) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()

    return resp.json()["rate"]


def convert_to_usd(currency: str, amount: float, billing_date: str) -> float:
    rate = _get_usd_rate(currency, billing_date)
    return round(amount * rate, 2)


def convert_pdf_to_images(pdf_bytes: bytes) -> List[str]:
    images = convert_from_bytes(pdf_bytes, last_page=5)

    if not images:
        return []

    b64_images = []
    for im in images:
        buffered = io.BytesIO()
        im.save(buffered, format="JPEG")
        b64_images.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))

    return b64_images


def extract_and_structure_from_images(
    images_b64: List[str],
) -> LLMExtractionReturnType:
    with open("core/features/ingestion/extraction_prompt.txt", "r") as f:
        system_prompt = f.read()

    content: List[dict] = []
    for i, img in enumerate(images_b64):
        page_label = f"Page {i + 1}:"
        content.append({"type": "text", "text": page_label})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"},
            }
        )

    try:
        response = groq.beta.chat.completions.parse(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},  # type: ignore
            ],
            response_format=LLMExtractionReturnType,
        )
    except Exception as e:
        # Handle API errors concisely
        error_msg = str(e)
        if "json_validate_failed" in error_msg:
            raise Exception(
                "LLM output failed schema validation. Check model types/quantities."
            )
        raise e

    parsed = response.choices[0].message.parsed
    if parsed is None:
        refusal = getattr(response.choices[0].message, "refusal", None)
        raise Exception(f"Failed to structure extracted text. Refusal: {refusal}")

    return parsed
