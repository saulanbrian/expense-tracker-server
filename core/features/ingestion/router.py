from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, WebSocket
import json

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


@router.websocket("/ws/{job_id}")
async def ws(job_id: str, websocket: WebSocket):
    redis = websocket.app.state.redis
    await websocket.accept()

    pubsub = redis.pubsub()
    await pubsub.subscribe(job_id)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"].decode("utf-8"))
                await websocket.send_json(data)
    except Exception as e:
        print(e)
