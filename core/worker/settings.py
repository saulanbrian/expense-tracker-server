import os

from arq.connections import RedisSettings
from arq.typing import WorkerSettingsBase

from core.features.ingestion.pipeline.task import ingest_document

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")


class WorkerSettings(WorkerSettingsBase):
    functions = [ingest_document]
    redis_settings = RedisSettings(host=REDIS_HOST, port=6379)
