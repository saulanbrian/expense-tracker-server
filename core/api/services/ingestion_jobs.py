import datetime

from core.api.schemas import IngestionJob
from core.supabase import supabase_client as supabase


def create_ingestion_job(document_id: str) -> IngestionJob:
    response = (
        supabase.table("ingestion_jobs")
        .insert({"document_id": document_id, "status": "queued"})
        .execute()
    )
    if not response.data:
        raise Exception("Failed to create ingestion job")
    return IngestionJob.model_validate(response.data[0])


def get_latest_ingestion_job(document_id: str) -> IngestionJob | None:
    response = (
        supabase.table("ingestion_jobs")
        .select("*")
        .eq("document_id", document_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return IngestionJob.model_validate(response.data[0])


def _update(job_id: str, updates: dict) -> None:
    supabase.table("ingestion_jobs").update(updates).eq("id", job_id).execute()


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def mark_running(job_id: str) -> None:
    _update(job_id, {"status": "running", "started_at": _now()})


def update_step(job_id: str, step: str) -> None:
    _update(job_id, {"current_step": step})


def mark_completed(job_id: str) -> None:
    _update(job_id, {"status": "completed", "completed_at": _now()})


def mark_failed(job_id: str, reason: str) -> None:
    _update(
        job_id, {"status": "failed", "failure_reason": reason, "completed_at": _now()}
    )


def mark_cancelled(job_id: str, reason: str) -> None:
    _update(
        job_id,
        {"status": "cancelled", "failure_reason": reason, "completed_at": _now()},
    )
