from fastapi import APIRouter, Request

from domain.schemas import DocumentsUpdate
from services.ingestion_jobs import create_ingestion_job, get_latest_ingestion_job
from services.documents import update_document

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"],
)

ACTIVE_STATUSES = {"queued", "running"}


@router.post("/")
async def process_document(document_id: str, request: Request):
    existing_job = get_latest_ingestion_job(document_id)

    if existing_job and existing_job.status in ACTIVE_STATUSES:
        return {
            "task_id": existing_job.id,
            "duplicate": True,
            "message": "A job is already in progress for this document",
        }

    job = create_ingestion_job(document_id)
    update_document(document_id, DocumentsUpdate(status="queued"))
    await request.app.state.arq_redis.enqueue_job("ingest_document", document_id, job.id)
    return {"task_id": job.id, "duplicate": False}
