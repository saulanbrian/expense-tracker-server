import base64
import io
from typing import List

from pdf2image import convert_from_bytes

from core.api.services import download_document_file
from core.ocr import ocr_from_images


def _pdf_to_images(pdf_bytes: bytes) -> List[str]:
    images = convert_from_bytes(pdf_bytes, last_page=5)
    if not images:
        return []
    b64_images = []
    for im in images:
        buffered = io.BytesIO()
        im.save(buffered, format="JPEG")
        b64_images.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))
    return b64_images


def _pdf_to_raw_images(pdf_bytes: bytes) -> List[bytes]:
    images = convert_from_bytes(pdf_bytes, last_page=5)
    if not images:
        return []
    raw_images = []
    for im in images:
        buffered = io.BytesIO()
        im.save(buffered, format="JPEG")
        raw_images.append(buffered.getvalue())
    return raw_images


async def download_file(storage_path: str) -> bytes:
    return download_document_file(storage_path)


async def convert_to_images(file_bytes: bytes, file_type: str) -> List[str]:
    if file_type == "application/pdf":
        return _pdf_to_images(file_bytes)
    if file_type in ["image/jpeg", "image/png", "image/webp"]:
        return [base64.b64encode(file_bytes).decode("utf-8")]
    raise ValueError(f"Unsupported file type: {file_type}")


def _get_raw_images(file_bytes: bytes, file_type: str) -> List[bytes]:
    if file_type == "application/pdf":
        return _pdf_to_raw_images(file_bytes)
    if file_type in ["image/jpeg", "image/png", "image/webp"]:
        return [file_bytes]
    raise ValueError(f"Unsupported file type: {file_type}")


async def run_analyzing_phase(ctx, update_status):
    phase = "analyzing_document"
    await update_status(phase, "in_progress")

    file_bytes = await download_file(ctx["document"].storage_path)
    images_b64 = await convert_to_images(file_bytes, ctx["document"].file_type)

    raw_images = _get_raw_images(file_bytes, ctx["document"].file_type)
    extracted_text = ocr_from_images(raw_images)

    ctx["file_bytes"] = file_bytes
    ctx["images_b64"] = images_b64
    ctx["extracted_text"] = extracted_text

    await update_status(phase, "completed")
