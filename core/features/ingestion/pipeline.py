import base64
import inspect
import traceback
from typing import Any, List

from core.api.schema_public_latest import (
    DocumentLineItemsInsert,
    Documents,
    DocumentsUpdate,
)
from core.features.ingestion.services import (
    download_document_file,
    get_document,
    insert_document_line_item,
    update_document,
)
from core.features.ingestion.utils import (
    _get_usd_rate,
    convert_pdf_to_images,
    extract_and_structure_from_images,
)


class IngestionPipeline:
    def __init__(self, ctx: Any, document_id: str):
        self.ctx = ctx
        self.document_id = document_id
        self.current_step: str = ""

        self.document: Any = None
        self.file_bytes: bytes = b""
        self.images_b64: List[str] = []
        self.structured_data: Any = None

    async def _run_step(self, step_name: str, func, *args, **kwargs):
        self.current_step = step_name
        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            return result
        except Exception as e:
            print(f"Error in step '{step_name}':", flush=True)
            traceback.print_exc()
            raise e

    async def retrieve_and_lock(self):
        response = await self._run_step(
            "retrieving_document", get_document, self.document_id
        )
        if not response.data:
            raise Exception(f"Document {self.document_id} not found in database")

        self.document = Documents.model_validate(response.data[0])
        if self.document.status in ["processing", "extracted", "verified"]:
            return False  # Signal to ignore

        await self._run_step(
            "locking_document",
            update_document,
            self.document_id,
            DocumentsUpdate(status="processing"),
        )
        return True

    async def download(self):
        self.file_bytes = await self._run_step(
            "downloading_file", download_document_file, self.document.storage_path
        )

    async def convert(self):
        if self.document.file_type == "application/pdf":
            self.images_b64 = await self._run_step(
                "converting_pdf_file", convert_pdf_to_images, self.file_bytes
            )

        elif self.document.file_type in ["image/jpeg", "image/png", "image/webp"]:

            def encode_raw_image():
                return [base64.b64encode(self.file_bytes).decode("utf-8")]

            self.images_b64 = await self._run_step(
                "encoding_raw_image", encode_raw_image
            )
        else:
            raise ValueError(f"Unsupported file type: {self.document.file_type}")

    async def extract_and_structure(self):
        self.structured_data = await self._run_step(
            "extracting_and_structuring_data",
            extract_and_structure_from_images,
            self.images_b64,
        )

    async def set_failed(self, error_message: str):
        await self._run_step(
            "marking_failed",
            update_document,
            self.document_id,
            DocumentsUpdate(status="failed", error_message=error_message),
        )

    async def save_to_db(self) -> str:
        if not self.structured_data.is_financial_billing:
            await self._run_step(
                "updating_document_status",
                update_document,
                self.document_id,
                DocumentsUpdate(status="failed", error_message="File is not a valid financial billing document"),
            )
            return "failed"

        doc_fields = self.structured_data.document.model_dump(exclude_unset=True) if self.structured_data.document else {}

        doc = self.structured_data.document
        if doc and doc.currency and doc.total_amount and doc.invoice_date:
            try:
                rate = _get_usd_rate(doc.currency, doc.invoice_date)
                doc_fields["usd_rate_as_of_billing_date"] = rate
                doc_fields["usd_conversion_total"] = round(doc.total_amount * rate, 2)
            except Exception:
                pass

        doc_updates = DocumentsUpdate(status="extracted", **doc_fields)
        await self._run_step("update_document", update_document, self.document_id, doc_updates)

        if self.structured_data.document_line_items:
            for item in self.structured_data.document_line_items:
                line_item = DocumentLineItemsInsert(
                    document_id=self.document.id,
                    **item.model_dump(exclude_unset=True),
                )
                await self._run_step(
                    "saving_document_line_item",
                    insert_document_line_item,
                    line_item,
                )

        return "success"
