import base64
import io

from pdf2image import convert_from_bytes

from domain.schemas import PipelineContext
from infra.ocr import ocr_from_images
from services.documents import download_document_file

SUPPORTED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
MAX_PDF_PAGES = 5


def _pdf_to_images(pdf_bytes: bytes) -> list[str]:
    images = convert_from_bytes(pdf_bytes, last_page=MAX_PDF_PAGES)
    if not images:
        return []
    b64_images = []
    for im in images:
        buffered = io.BytesIO()
        im.save(buffered, format="JPEG")
        b64_images.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))
    return b64_images


def _pdf_to_raw_images(pdf_bytes: bytes) -> list[bytes]:
    images = convert_from_bytes(pdf_bytes, last_page=MAX_PDF_PAGES)
    if not images:
        return []
    raw_images = []
    for im in images:
        buffered = io.BytesIO()
        im.save(buffered, format="JPEG")
        raw_images.append(buffered.getvalue())
    return raw_images


def _to_images(file_bytes: bytes, file_type: str) -> list[str]:
    if file_type == "application/pdf":
        return _pdf_to_images(file_bytes)
    if file_type in SUPPORTED_IMAGE_MIMES:
        return [base64.b64encode(file_bytes).decode("utf-8")]
    raise ValueError(f"Unsupported file type: {file_type}")


def _to_raw_images(file_bytes: bytes, file_type: str) -> list[bytes]:
    if file_type == "application/pdf":
        return _pdf_to_raw_images(file_bytes)
    if file_type in SUPPORTED_IMAGE_MIMES:
        return [file_bytes]
    raise ValueError(f"Unsupported file type: {file_type}")


async def run_convert(ctx: PipelineContext, update_status) -> None:
    phase = "converting_document"
    await update_status(phase, "in_progress")

    assert ctx.document is not None
    file_bytes = download_document_file(ctx.document.storage_path)
    images_b64 = _to_images(file_bytes, ctx.document.file_type)
    raw_images = _to_raw_images(file_bytes, ctx.document.file_type)
    ocr_texts = ocr_from_images(raw_images)
    extracted_text = "\n".join(ocr_texts) if isinstance(ocr_texts, list) else ocr_texts

    ctx.file_bytes = file_bytes
    ctx.images_b64 = images_b64
    ctx.extracted_text = extracted_text

    await update_status(phase, "completed")
