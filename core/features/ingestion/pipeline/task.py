import traceback

from core.api.schemas import DocumentsUpdate
from core.api.services import (
    mark_cancelled,
    mark_completed,
    mark_failed,
    mark_running,
    update_document,
    update_step,
)
from core.features.ingestion.pipeline.phases import (
    run_analyzing_phase,
    run_drafting_phase,
    run_extraction_phase,
    run_retrieval_phase,
)


async def ingest_document(ctx, document_id: str, job_id: str):
    pipe_ctx = {
        "document_id": document_id,
        "document": None,
        "file_bytes": None,
        "images_b64": None,
        "extracted_text": None,
        "structured_data": None,
        "should_ignore": False,
        "extraction_reason": None,
    }

    async def update_status(phase, status):
        if status == "in_progress":
            update_step(job_id, phase)

    try:
        mark_running(job_id)
        await run_retrieval_phase(pipe_ctx, update_status)

        if pipe_ctx["should_ignore"]:
            mark_cancelled(
                job_id,
                "document is either already ingested or ingestion already extracted",
            )
            return {"ingestion_status": "ignored"}

        await run_analyzing_phase(pipe_ctx, update_status)
        await run_extraction_phase(pipe_ctx, update_status)
        await run_drafting_phase(pipe_ctx, update_status)

        mark_completed(job_id)
        return {"ingestion_status": "success"}

    except Exception as e:
        traceback.print_exc()
        mark_failed(job_id, str(e))
        update_document(
            document_id,
            DocumentsUpdate(status="failed", error_message=str(e)),
        )
        return {"ingestion_status": "failed"}
