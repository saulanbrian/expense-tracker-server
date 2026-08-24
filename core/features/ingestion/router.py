from arq.connections import ArqRedis
from fastapi import APIRouter, Depends

from core.api.schemas import DocumentsUpdate
from core.api.services import create_ingestion_job, update_document
from core.api.services.ingestion_jobs import get_latest_ingestion_job
from core.dependencies import get_redis_pool

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"],
)

ACTIVE_STATUSES = {"queued", "running"}


@router.post("/")
async def process_document(
    document_id: str, redis_pool: ArqRedis = Depends(get_redis_pool)
):
    existing_job = get_latest_ingestion_job(document_id)

    if existing_job and existing_job.status in ACTIVE_STATUSES:
        return {
            "task_id": existing_job.id,
            "duplicate": True,
            "message": "A job is already in progress for this document",
        }

    job = create_ingestion_job(document_id)
    update_document(document_id, DocumentsUpdate(status="queued"))
    await redis_pool.enqueue_job("ingest_document", document_id, job.id)
    return {"task_id": job.id, "duplicate": False}
