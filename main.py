import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as aioredis
from arq import create_pool as create_arq_pool
from arq.connections import RedisSettings
from core.api.router import api_router

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_pool = aioredis.ConnectionPool.from_url(f"redis://{REDIS_HOST}:6379/0")

    app.state.redis = aioredis.Redis(connection_pool=redis_pool)

    app.state.arq_redis = await create_arq_pool(
        RedisSettings(host=REDIS_HOST, port=6379)
    )

    yield

    await app.state.redis.close()
    await app.state.arq_redis.close()
    await redis_pool.disconnect()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
