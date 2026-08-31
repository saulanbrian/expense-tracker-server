import logging

from domain.schemas import DocumentsUpdate, PipelineContext
from features.ingestion.pipeline.phases import (
    run_convert,
    run_enrich,
    run_extract,
    run_load,
    run_persist,
)
from services.documents import update_document
from services.ingestion_jobs import (
    mark_cancelled,
    mark_completed,
    mark_failed,
    mark_running,
    update_step,
)

logger = logging.getLogger(__name__)


async def ingest_document(ctx, document_id: str, job_id: str):
    pipe_ctx = PipelineContext(document_id=document_id)

    async def update_status(phase: str, status: str):
        if status == "in_progress":
            update_step(job_id, phase)

    try:
        mark_running(job_id)
        load_result = await run_load(pipe_ctx, update_status)

        if not load_result.should_process:
            mark_cancelled(
                job_id,
                "document is either already ingested or ingestion already extracted",
            )
            return {"ingestion_status": "ignored"}

        await run_convert(pipe_ctx, update_status)
        await run_extract(pipe_ctx, update_status)
        await run_enrich(pipe_ctx, update_status)
        await run_persist(pipe_ctx, update_status)

        mark_completed(job_id)
        return {"ingestion_status": "success"}

    except Exception as e:
        logger.exception("Ingestion failed for document %s", document_id)
        mark_failed(job_id, str(e))
        update_document(
            document_id,
            DocumentsUpdate(status="failed", error_message=str(e)),
        )
        return {"ingestion_status": "failed"}
