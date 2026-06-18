from typing import List, Optional, Annotated
from pydantic import BaseModel, Field


class StrippedDocument(BaseModel):
    currency: Optional[str] = Field(default=None)
    due_date: Optional[str] = Field(
        default=None, description="The due date in YYYY-MM-DD format"
    )
    invoice_date: Optional[str] = Field(
        default=None, description="The invoice date in YYYY-MM-DD format"
    )
    invoice_number: Optional[str] = Field(default=None)
    subtotal: Optional[float] = Field(default=None)
    tax_amount: Optional[float] = Field(default=None)
    total_amount: Optional[float] = Field(default=None)
    vendor_name: Optional[str] = Field(default=None)


class StrippedDocumentLineItem(BaseModel):
    description: str = Field(description="The description of the line item")
    quantity: Optional[float] = Field(default=None)
    total_price: float = Field(description="The total price for this line item")
    unit_price: Optional[float] = Field(default=None)
    page_number: int = Field(description="The 1-based page number where this line item is found")
    bounding_box: Annotated[List[float], Field(min_length=4, max_length=4)] = Field(
        description="The normalized bounding box coordinates [ymin, xmin, ymax, xmax] from 0 to 1000. MUST be exactly 4 numbers. Do not provide 8 numbers.",
    )


class LLMExtractionReturnType(BaseModel):
    is_financial_billing: bool = Field(
        description="set this to True if this is a financial billing document, otherwise False"
    )
    layout_description: str = Field(
        description="A brief description of the document's visual layout (e.g., 'multi-column', 'scattered key-value pairs', 'standard table'). Analyze how the data is organized before extracting."
    )
    document: Optional[StrippedDocument] = Field(
        description="the document header information"
    )
    document_line_items: Optional[List[StrippedDocumentLineItem]] = Field(
        description="the document line items"
    )
