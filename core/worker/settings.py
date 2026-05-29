from arq.typing import WorkerSettingsBase

from core.features.ingestion.tasks import ingest_document


class WorkerSettings(WorkerSettingsBase):
    functions = [ingest_document]
