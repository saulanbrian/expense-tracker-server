import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from arq import create_pool as create_arq_pool
from arq.connections import RedisSettings
from features.ingestion.router import router as api_router

def _redis_settings() -> RedisSettings:
    url = os.getenv("REDIS_URL")
    if url:
        return RedisSettings.from_dsn(url)
    return RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_redis = await create_arq_pool(_redis_settings())
    yield
    await app.state.arq_redis.close()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
