from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import UUID4, BaseModel, Field


class Documents(BaseModel):
    id: UUID4
    organization_id: UUID4
    uploaded_by: UUID4 | None = None
    storage_path: str
    file_name: str
    file_type: str
    file_size_bytes: int
    status: str | None = "uploaded"
    error_message: str | None = None
    vendor_name: str | None = None
    invoice_number: str | None = None
    invoice_date: datetime.date | None = None
    due_date: datetime.date | None = None
    currency: str | None = "USD"
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    usd_rate_as_of_billing_date: Decimal | None = None
    usd_conversion_total: Decimal | None = None


class DocumentsUpdate(BaseModel):
    id: UUID4 | None = None
    organization_id: UUID4 | None = None
    uploaded_by: UUID4 | None = None
    storage_path: str | None = None
    file_name: str | None = None
    file_type: str | None = None
    file_size_bytes: int | None = None
    status: str | None = None
    error_message: str | None = None
    vendor_name: str | None = None
    invoice_number: str | None = None
    invoice_date: datetime.date | None = None
    due_date: datetime.date | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
    updated_at: datetime.datetime | None = None
    usd_rate_as_of_billing_date: Decimal | None = None
    usd_conversion_total: Decimal | None = None


class DocumentLineItemsInsert(BaseModel):
    document_id: UUID4
    description: str
    quantity: Decimal | None = 1.0
    unit_price: Decimal | None = None
    total_price: Decimal
    gl_code: str | None = None
    page_number: int | None = 1


class IngestionJob(BaseModel):
    id: UUID4 | None = None
    document_id: UUID4 | None = None
    status: str | None = None
    progress: int | None = 0
    current_step: str | None = None
    failure_reason: str | None = None
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
