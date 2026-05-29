from arq import create_pool
from fastapi import FastAPI
from arq.connections import RedisSettings
from core.api.router import api_router

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


app.include_router(api_router)
