from core.api.schema_public_latest import Documents, DocumentsUpdate
from core.api.services import get_document, update_document
from core.features.ingestion.pipeline.tracker import run_step


async def retrieve_document(document_id: str) -> Documents:
    response = get_document(document_id)
    if not response.data:
        raise Exception(f"Document {document_id} not found in database")
    return Documents.model_validate(response.data[0])


async def should_process(document: Documents) -> bool:
    return document.status not in ["processing", "extracted", "verified"]


async def lock_document(document_id: str) -> None:
    update_document(document_id, DocumentsUpdate(status="processing"))


async def run_retrieval_phase(ctx, tracker, publish):
    phase = "retrieving_document_information"
    await publish(phase, "in_progress")

    ctx["document"] = await run_step(
        tracker, phase, "retrieve_document", retrieve_document, ctx["document_id"]
    )
    ctx["should_ignore"] = not await run_step(
        tracker, phase, "should_process", should_process, ctx["document"]
    )

    if not ctx["should_ignore"]:
        await run_step(
            tracker, phase, "lock_document", lock_document, ctx["document_id"]
        )

    await publish(phase, "completed")
