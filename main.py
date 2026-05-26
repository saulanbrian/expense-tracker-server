from arq import create_pool
from fastapi import FastAPI
from arq.connections import RedisSettings


app = FastAPI()
redis = RedisSettings()


@app.on_event("startup")
async def startup():
    app.state.redis = await create_pool(
        RedisSettings(
            host="localhost",
            port=6379,
        )
    )


@app.on_event("shutdown")
async def shutdown():
    await app.state.redis.close()


@app.post("/ingest_document")
async def root(document_id: str):
    job_id = await app.state.redis.enqueue_job("ingest_document", document_id)
    return {"message": "hello"}
