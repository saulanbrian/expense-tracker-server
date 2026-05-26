from arq.typing import WorkerSettingsBase

from core.features.ingestion.services.ingest_document import ingest_document


class WorkerSettings(WorkerSettingsBase):
    functions = [ingest_document]
