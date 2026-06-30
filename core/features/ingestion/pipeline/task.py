import json
import traceback

from core.api.schema_public_latest import DocumentsUpdate
from core.api.services import update_document
from core.features.ingestion.pipeline.phases import (
    run_analyzing_phase,
    run_drafting_phase,
    run_extraction_phase,
    run_retrieval_phase,
)
from core.features.ingestion.pipeline.tracker import PhaseTracker


async def ingest_document(ctx, document_id: str):
    pipe_ctx = {
        "document_id": document_id,
        "document": None,
        "file_bytes": None,
        "images_b64": None,
        "structured_data": None,
        "should_ignore": False,
    }

    tracker = PhaseTracker()

    async def publish(phase, status):
        await ctx["redis"].publish(
            ctx["job_id"],
            json.dumps({"pipeline_stage": phase, "stage_status": status}),
        )

    try:
        await run_retrieval_phase(pipe_ctx, tracker, publish)

        if pipe_ctx["should_ignore"]:
            await ctx["redis"].publish(
                ctx["job_id"],
                json.dumps(
                    {
                        "status": "ignored",
                        "reason": "document is either already ingested or ingestion already extracted",
                    }
                ),
            )
            return {"ingestion_status": "ignored"}

        await run_analyzing_phase(pipe_ctx, tracker, publish)
        await run_extraction_phase(pipe_ctx, tracker, publish)
        await run_drafting_phase(pipe_ctx, tracker, publish)

        return {"ingestion_status": "success"}

    except Exception as e:
        traceback.print_exc()
        await publish(tracker.current_phase, "failed")
        update_document(
            document_id,
            DocumentsUpdate(status="failed", error_message=str(e)),
        )
        return {"ingestion_status": "failed"}
