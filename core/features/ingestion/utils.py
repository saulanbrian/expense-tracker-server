from dotenv import load_dotenv
import os
import base64
import json
import io
import numpy as np
from typing import List, Optional
from PIL import Image
from pdf2image import convert_from_bytes
from rapidocr_onnxruntime import RapidOCR

from core.api.schema_public_latest import Documents
from core.openai import groq
from .models import LLMExtractionReturnType

load_dotenv()

# Global OCR engine initialized lazily
_ocr_engine: Optional[RapidOCR] = None


def get_ocr_engine() -> RapidOCR:
    global _ocr_engine
    if _ocr_engine is None:
        # Initialize RapidOCR engine
        _ocr_engine = RapidOCR()
    return _ocr_engine


def get_ocr_data(images_b64: List[str]) -> List[List[dict]]:
    """
    Performs OCR on base64 images and returns a list of pages,
    where each page is a list of detected text blocks with boxes.
    """
    ocr = get_ocr_engine()
    results = []

    for img_b64 in images_b64:
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        
        # Resize image if it's too large to save memory
        max_size = 1600
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        img_np = np.array(img)

        # RapidOCR returns list of (box, text, confidence)
        # box is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        ocr_result, _ = ocr(img_np)

        page_items = []
        if ocr_result:
            width, height = img.size

            for box, text, confidence in ocr_result:
                # box is already a list of 4 points [[x,y],...]
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]

                ymin, xmin, ymax, xmax = min(ys), min(xs), max(ys), max(xs)

                # Normalized to 0-1000
                norm_box = [
                    int(max(0, min(1000, ymin / height * 1000))),
                    int(max(0, min(1000, xmin / width * 1000))),
                    int(max(0, min(1000, ymax / height * 1000))),
                    int(max(0, min(1000, xmax / width * 1000))),
                ]

                page_items.append(
                    {
                        "text": text,
                        "confidence": float(confidence),
                        "box_2d": box,  # Raw coordinates
                        "normalized_box": norm_box,  # 0-1000 [ymin, xmin, ymax, xmax]
                    }
                )
        results.append(page_items)

    return results


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
    ocr_data: Optional[List[List[dict]]] = None,
) -> LLMExtractionReturnType:
    with open("core/features/ingestion/extraction_prompt.txt", "r") as f:
        system_prompt = f.read()

    content: List[dict] = []
    for i, img in enumerate(images_b64):
        page_label = f"Page {i + 1}:"
        content.append({"type": "text", "text": page_label})

        if ocr_data and i < len(ocr_data):
            # Include OCR text and boxes for this page to assist LLM
            ocr_text_blocks = []
            for item in ocr_data[i]:
                ocr_text_blocks.append(
                    f"Text: '{item['text']}' | Box: {item['normalized_box']}"
                )

            if ocr_text_blocks:
                content.append(
                    {
                        "type": "text",
                        "text": f"OCR Data for {page_label}:\n"
                        + "\n".join(ocr_text_blocks),
                    }
                )

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
            raise Exception("LLM output failed schema validation. Check model types/quantities.")
        raise e

    parsed = response.choices[0].message.parsed
    if parsed is None:
        refusal = getattr(response.choices[0].message, "refusal", None)
        raise Exception(f"Failed to structure extracted text. Refusal: {refusal}")

    return parsed
