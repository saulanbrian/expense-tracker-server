from typing import List
from core.api.schema_public_latest import (
    DocumentLineItemsInsert,
    Documents,
    DocumentsBaseSchema,
    DocumentsUpdate,
)
from .services import update_document, insert_document_line_item, get_document
import base64
from core.features.ingestion.models import (
    StrippedDocument,
    StrippedDocumentLineItem,
)
from core.supabase import supabase_client as supabase
from core.features.ingestion.utils import (
    extract_text_from_document,
    structure_extracted_text,
    convert_pdf_to_image,
)


async def ingest_document(ctx, document_id: str):

    response = get_document(document_id)
    if not response.data:
        return {"status": "error", "message": "Document not found"}

    document: Documents = Documents.model_validate(response.data[0])

    if document.status in ["processing", "extracted"]:
        return {"status": "ignored"}

    try:
        update_document(document_id, DocumentsUpdate(status="processing"))

    except Exception as e:
        print(e)
        return {"status": "error"}

    try:
        file_bytes = supabase.storage.from_("documents").download(document.storage_path)

        if document.file_type == "application/pdf":
            image_b64 = convert_pdf_to_image(file_bytes)
        else:
            image_b64 = base64.b64encode(file_bytes).decode("utf-8")

        text = extract_text_from_document(image_b64)
        structured_data = structure_extracted_text(text)

        if not structured_data.is_financial_billing:
            update_document(
                document_id,
                DocumentsUpdate(
                    status="failed", error_message="Not a financial document"
                ),
            )
            return {"status": "ignored"}

        structured_document: StrippedDocument = structured_data.document  # type: ignore
        document_line_items: List[StrippedDocumentLineItem] = (
            structured_data.document_line_items
        )  # type: ignore

        update_document(
            document_id,
            DocumentsUpdate(
                status="extracted", **structured_document.model_dump(mode="json")
            ),
        )

        if document_line_items:
            for line_item in document_line_items:
                item = DocumentLineItemsInsert(
                    **line_item.model_dump(), document_id=document.id
                )
                insert_document_line_item(item)

        return {"status": "success"}

    except Exception as e:
        print(e)
        update_document(
            document_id, DocumentsUpdate(status="failed", error_message=str(e))
        )
        return {"status": "error"}
