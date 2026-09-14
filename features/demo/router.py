import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from domain.schemas import Documents, DocumentsUpdate
from services.documents import insert_document, update_document, upload_document_file
from services.ingestion_jobs import create_ingestion_job

router = APIRouter(
    prefix="/demo",
    tags=["demo"],
)

DEMO_ORG_ID = uuid.UUID("9f720db8-3dd4-407e-97c9-d53cc3527fb3")
ALLOWED_MIMES = {"application/pdf", "image/jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/ingestion/")
async def demo_ingest(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, JPEG.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")

    doc_id = uuid.uuid4()
    file_name = file.filename or "unnamed"
    storage_path = f"demo/{doc_id}_{file_name}"

    upload_document_file(storage_path, file_bytes, file.content_type)

    document = Documents(
        id=doc_id,
        organization_id=DEMO_ORG_ID,
        storage_path=storage_path,
        file_name=file_name,
        file_type=file.content_type,
        file_size_bytes=len(file_bytes),
    )
    insert_document(document)

    job = create_ingestion_job(str(doc_id))
    update_document(str(doc_id), DocumentsUpdate(status="queued"))
    await request.app.state.arq_redis.enqueue_job("ingest_document", str(doc_id), job.id)

    return {"document_id": str(doc_id), "job_id": job.id}
