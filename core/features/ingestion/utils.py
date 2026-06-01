from dotenv import load_dotenv
import os
import base64
from core.api.schema_public_latest import Documents
from core.openai import groq
from .models import LLMExtractionReturnType

from PIL import Image
from pdf2image import convert_from_bytes
import io

load_dotenv()


def convert_pdf_to_image(pdf_bytes: bytes) -> str:
    images = convert_from_bytes(pdf_bytes, last_page=5)

    if not images:
        return ""

    # Stack images vertically
    widths, heights = zip(*(i.size for i in images))
    max_width = max(widths)
    total_height = sum(heights)

    new_im = Image.new("RGB", (max_width, total_height))

    y_offset = 0
    for im in images:
        new_im.paste(im, (0, y_offset))
        y_offset += im.size[1]

    # Convert to base64
    buffered = io.BytesIO()
    new_im.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def extract_text_from_document(image_b64: str) -> str:

    response = groq.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [  # type: ignore
                    {
                        "type": "text",
                        "text": (
                            "You are an expert document analyzer. "
                            "Extract all text from the document and return it as a single string. "
                            "Note: This is an expense tracker. If the document is not related to financial expenses, "
                            "receipts, or invoices, do not bother extracting anything and just return 'NOT_AN_EXPENSE'."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
    )

    return response.choices[0].message.content or ""


def structure_extracted_text(text: str) -> LLMExtractionReturnType:

    if text == "NOT_AN_EXPENSE":
        return LLMExtractionReturnType(
            is_financial_billing=False, document=None, document_line_items=None
        )

    with open("core/features/ingestion/extraction_prompt.txt", "r") as f:
        system_prompt = f.read()

    response = groq.beta.chat.completions.parse(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        response_format=LLMExtractionReturnType,
    )

    parsed = response.choices[0].message.parsed
    if parsed is None:
        refusal = getattr(response.choices[0].message, "refusal", None)
        if refusal:
            print(f"Model refusal: {refusal}")
        else:
            print(
                f"Failed to parse LLM output. Content: {response.choices[0].message.content}"
            )
        raise Exception("Failed to structure extracted text")

    return parsed  # type: ignore
