from arq.connections import ArqRedis
from fastapi import APIRouter, Depends

from core.dependencies import get_redis_pool

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"],
)


@router.post("/")
async def process_document(
    document_id: str, redis_pool: ArqRedis = Depends(get_redis_pool)
):
    task = await redis_pool.enqueue_job("ingest_document", document_id)
    return {"task_id": task.job_id}
