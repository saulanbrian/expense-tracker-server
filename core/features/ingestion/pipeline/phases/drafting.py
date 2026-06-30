from typing import Any, Dict
from uuid import UUID

import httpx

from core.api.schema_public_latest import (
    DocumentLineItemsInsert,
    DocumentsUpdate,
)
from core.api.services import (
    insert_document_line_item,
    update_document,
)
from core.features.ingestion.pipeline.models import LLMExtractionReturnType
from core.features.ingestion.pipeline.tracker import run_step

FRANKFURTER_API = "https://api.frankfurter.dev"


def _get_usd_rate(currency: str, billing_date: str) -> float:
    currency = currency.upper().strip()
    if currency == "USD":
        return 1.0
    url = f"{FRANKFURTER_API}/v2/rate/{currency}/USD"
    params = {"date": billing_date}
    with httpx.Client(timeout=10) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
    return resp.json()["rate"]


async def validate_document(data: LLMExtractionReturnType) -> None:
    if not data.is_financial_billing:
        raise ValueError("File is not a valid financial billing document")


async def enrich_document(data: LLMExtractionReturnType) -> Dict[str, Any]:
    doc_fields: Dict[str, Any] = (
        data.document.model_dump(exclude_unset=True) if data.document else {}
    )
    doc = data.document
    if doc and doc.currency and doc.total_amount and doc.invoice_date:
        try:
            rate = _get_usd_rate(doc.currency, doc.invoice_date)
            doc_fields["usd_rate_as_of_billing_date"] = rate
            doc_fields["usd_conversion_total"] = round(doc.total_amount * rate, 2)
        except Exception:
            pass
    return doc_fields


async def save_document(document_id: str, doc_fields: Dict[str, Any]) -> None:
    doc_updates = DocumentsUpdate(status="extracted", **doc_fields)
    update_document(document_id, doc_updates)


async def save_line_items(document_id: UUID, data: LLMExtractionReturnType) -> None:
    if not data.document_line_items:
        return
    for item in data.document_line_items:
        line_item = DocumentLineItemsInsert(
            document_id=document_id,
            **item.model_dump(exclude_unset=True),
        )
        insert_document_line_item(line_item)


async def run_drafting_phase(ctx, tracker, publish):
    phase = "drafting_document"
    await publish(phase, "in_progress")

    await run_step(
        tracker, phase, "validate_document", validate_document, ctx["structured_data"]
    )
    doc_fields = await run_step(
        tracker, phase, "enrich_document", enrich_document, ctx["structured_data"]
    )
    await run_step(
        tracker, phase, "save_document", save_document, ctx["document_id"], doc_fields
    )
    await run_step(
        tracker,
        phase,
        "save_line_items",
        save_line_items,
        ctx["document"].id,
        ctx["structured_data"],
    )

    await publish(phase, "completed")
