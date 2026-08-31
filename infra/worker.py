import os

from arq.connections import RedisSettings
from arq.typing import WorkerSettingsBase

from features.ingestion.pipeline.task import ingest_document


def _redis_settings() -> RedisSettings:
    url = os.getenv("REDIS_URL")
    if url:
        return RedisSettings.from_dsn(url)
    return RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )


class WorkerSettings(WorkerSettingsBase):
    functions = [ingest_document]
    redis_settings = _redis_settings()
    max_jobs = 2
