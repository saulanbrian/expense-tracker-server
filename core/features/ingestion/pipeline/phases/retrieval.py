from core.api.schemas import Documents, DocumentsUpdate
from core.api.services import get_document, update_document


async def retrieve_document(document_id: str) -> Documents:
    response = get_document(document_id)
    if not response.data:
        raise Exception(f"Document {document_id} not found in database")
    return Documents.model_validate(response.data[0])


async def should_process(document: Documents) -> bool:
    return document.status not in ["processing", "extracted", "verified"]


async def lock_document(document_id: str) -> None:
    update_document(document_id, DocumentsUpdate(status="processing"))


async def run_retrieval_phase(ctx, update_status):
    phase = "retrieving_document_information"
    await update_status(phase, "in_progress")

    ctx["document"] = await retrieve_document(ctx["document_id"])
    ctx["should_ignore"] = not await should_process(ctx["document"])

    if not ctx["should_ignore"]:
        await lock_document(ctx["document_id"])

    await update_status(phase, "completed")
