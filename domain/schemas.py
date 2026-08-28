from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

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


class StrippedDocument(BaseModel):
    currency: str | None = Field(default=None)
    due_date: str | None = Field(
        default=None, description="The due date in YYYY-MM-DD format"
    )
    invoice_date: str | None = Field(
        default=None, description="The invoice date in YYYY-MM-DD format"
    )
    invoice_number: str | None = Field(default=None)
    subtotal: float | None = Field(default=None)
    tax_amount: float | None = Field(default=None)
    total_amount: float | None = Field(default=None)
    vendor_name: str | None = Field(default=None)


class StrippedDocumentLineItem(BaseModel):
    description: str = Field(description="The description of the line item")
    quantity: float | None = Field(default=None)
    total_price: float = Field(description="The total price for this line item")
    unit_price: float | None = Field(default=None)
    page_number: int = Field(
        description="The 1-based page number where this line item is found"
    )


class LLMExtractionReturnType(BaseModel):
    needs_vision: bool = Field(
        default=False,
        description="Set to True if the text is garbled, incomplete, or appears to be from a scanned document that needs vision processing"
    )
    reason: str | None = Field(
        default=None,
        description="If needs_vision is True, explain why (e.g., 'Text appears garbled', 'Missing critical fields', 'Likely scanned document')"
    )
    is_financial_billing: bool = Field(
        description="set this to True if this is a financial billing document, otherwise False"
    )
    layout_description: str | None = Field(
        default=None,
        description="A brief description of the document's visual layout (e.g., 'multi-column', 'scattered key-value pairs', 'standard table'). Analyze how the data is organized before extracting."
    )
    document: StrippedDocument | None = Field(
        description="the document header information"
    )
    document_line_items: list[StrippedDocumentLineItem] | None = Field(
        description="the document line items"
    )


@dataclass
class LoadResult:
    """Result from the load phase — whether to continue the pipeline."""
    document: Documents
    should_process: bool


@dataclass
class PipelineContext:
    """Shared state threaded through all pipeline phases."""
    document_id: str
    document: Documents | None = None
    file_bytes: bytes | None = None
    images_b64: list[str] = field(default_factory=list)
    extracted_text: str = ""
    structured_data: LLMExtractionReturnType | None = None
    doc_fields: dict = field(default_factory=dict)
