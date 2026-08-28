from domain.schemas import Documents, DocumentsUpdate, LoadResult, PipelineContext
from services.documents import get_document, update_document


async def _fetch_document(document_id: str) -> Documents:
    response = get_document(document_id)
    if not response.data:
        raise Exception(f"Document {document_id} not found in database")
    return Documents.model_validate(response.data[0])


async def _should_process(document: Documents) -> bool:
    return document.status not in ["processing", "extracted", "verified"]


async def _lock_document(document_id: str) -> None:
    update_document(document_id, DocumentsUpdate(status="processing"))


async def run_load(ctx: PipelineContext, update_status) -> LoadResult:
    phase = "loading_document"
    await update_status(phase, "in_progress")

    document = await _fetch_document(ctx.document_id)
    should_process = await _should_process(document)

    if should_process:
        await _lock_document(ctx.document_id)

    ctx.document = document

    await update_status(phase, "completed")
    return LoadResult(document=document, should_process=should_process)
