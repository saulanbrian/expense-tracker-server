import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from arq import create_pool as create_arq_pool
from arq.connections import RedisSettings
from features.ingestion.router import router as api_router

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_redis = await create_arq_pool(
        RedisSettings(host=REDIS_HOST, port=6379)
    )
    yield
    await app.state.arq_redis.close()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
