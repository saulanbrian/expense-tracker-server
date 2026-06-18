import os
from arq.typing import WorkerSettingsBase
from arq.connections import RedisSettings
from core.features.ingestion.tasks import ingest_document

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

class WorkerSettings(WorkerSettingsBase):
    functions = [ingest_document]
    redis_settings = RedisSettings(host=REDIS_HOST, port=6379)
