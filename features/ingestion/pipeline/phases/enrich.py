import httpx

from domain.schemas import LLMExtractionReturnType, PipelineContext

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


def _enrich_doc_fields(data: LLMExtractionReturnType) -> dict:
    doc_fields = data.document.model_dump(exclude_unset=True) if data.document else {}
    doc = data.document
    if doc and doc.currency and doc.total_amount and doc.invoice_date:
        try:
            rate = _get_usd_rate(doc.currency, doc.invoice_date)
            doc_fields["usd_rate_as_of_billing_date"] = rate
            doc_fields["usd_conversion_total"] = round(doc.total_amount * rate, 2)
        except Exception:
            pass
    return doc_fields


async def run_enrich(ctx: PipelineContext, update_status) -> None:
    phase = "enriching_document"
    await update_status(phase, "in_progress")

    assert ctx.structured_data is not None
    if not ctx.structured_data.is_financial_billing:
        raise ValueError("File is not a valid financial billing document")

    ctx.doc_fields = _enrich_doc_fields(ctx.structured_data)

    await update_status(phase, "completed")
