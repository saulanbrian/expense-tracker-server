import base64
import inspect
from typing import Any, List
from core.api.schema_public_latest import (
    Documents,
    DocumentsUpdate,
    DocumentLineItemsInsert,
)
from core.features.ingestion.services import (
    get_document,
    update_document,
    download_document_file,
    insert_document_line_item,
)
from core.features.ingestion.utils import (
    convert_pdf_to_image,
    extract_text_from_document,
    structure_extracted_text,
)


class IngestionPipeline:
    def __init__(self, ctx: Any, document_id: str):
        self.ctx = ctx
        self.document_id = document_id
        self.current_step: str = ""

        self.document: Any = None
        self.file_bytes: bytes = b""
        self.image_b64: str = ""
        self.structured_data: Any = None
        self.text: str = ""

    async def _run_step(self, step_name: str, func, *args, **kwargs):
        self.current_step = step_name
        print(f"🚀 [Pipeline] Starting step: '{step_name}'...")
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def retrieve_and_lock(self):
        response = await self._run_step(
            "retrieving_document", get_document, self.document_id
        )
        if not response.data:
            raise Exception("Document not found")

        self.document = Documents.model_validate(response.data[0])
        if self.document.status in ["processing", "extracted", "verrified"]:
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
            self.image_b64 = await self._run_step(
                "converting_pdf_file", convert_pdf_to_image, self.file_bytes
            )

        elif self.document.file_type in ["image/jpeg", "image/png", "image/webp"]:

            def encode_raw_image():
                return base64.b64encode(self.file_bytes).decode("utf-8")

            self.image_b64 = await self._run_step(
                "encoding_raw_image", encode_raw_image
            )
        else:
            raise ValueError(f"Unsupported file type: {self.document.file_type}")

    async def extract_and_structure(self):
        self.text = await self._run_step(
            "extracting_text",
            extract_text_from_document,
            self.image_b64,
        )
        self.structured_data = await self._run_step(
            "structuring_data",
            structure_extracted_text,
            self.text,
        )

    async def save_to_db(self) -> str:
        if not self.structured_data.is_financial_billing:
            await self._run_step(
                "updating_document_status",
                update_document,
                self.document_id,
                DocumentsUpdate(
                    status="failed",
                    error_message="File is not a valid finnancial billing document",
                ),
            )
            return "failed"

        doc_updates = DocumentsUpdate(
            status="extracted",
            **self.structured_data.document.model_dump(exclude_unset=True),
        )
        await self._run_step(
            "update_document",
            update_document,
            self.document_id,
            doc_updates,
        )

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
