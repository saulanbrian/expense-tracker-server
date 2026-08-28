from uuid import UUID

from domain.schemas import DocumentLineItemsInsert, DocumentsUpdate, PipelineContext
from services.document_line_items import delete_document_line_items, insert_document_line_item
from services.documents import update_document


async def _save_document(document_id: str, doc_fields: dict) -> None:
    doc_updates = DocumentsUpdate(status="extracted", error_message=None, **doc_fields)
    update_document(document_id, doc_updates)


async def _save_line_items(document_id: UUID, ctx: PipelineContext) -> None:
    assert ctx.structured_data is not None
    delete_document_line_items(str(document_id))
    if not ctx.structured_data.document_line_items:
        return
    for item in ctx.structured_data.document_line_items:
        line_item = DocumentLineItemsInsert(
            document_id=document_id,
            **item.model_dump(exclude_unset=True),
        )
        insert_document_line_item(line_item)


async def run_persist(ctx: PipelineContext, update_status) -> None:
    phase = "persisting_document"
    await update_status(phase, "in_progress")

    assert ctx.document is not None
    assert ctx.structured_data is not None

    doc_fields = ctx.doc_fields
    await _save_document(ctx.document_id, doc_fields)
    await _save_line_items(ctx.document.id, ctx)

    await update_status(phase, "completed")
