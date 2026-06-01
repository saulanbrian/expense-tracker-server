from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import UUID4, BaseModel, Field

# CUSTOM CLASSES
# Note: These are custom model classes for defining common features among
# Pydantic Base Schema.


class CustomModel(BaseModel):
    """Base model class with common features."""

    pass


class CustomModelInsert(CustomModel):
    """Base model for insert operations with common features."""

    pass


class CustomModelUpdate(CustomModel):
    """Base model for update operations with common features."""

    pass


# BASE CLASSES
# Note: These are the base Row models that include all fields.


class DocumentLineItemsBaseSchema(CustomModel):
    """DocumentLineItems Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    description: str
    document_id: UUID4
    gl_code: str | None = Field(default=None)
    quantity: int | None = Field(default=None)
    total_price: Decimal
    unit_price: Decimal | None = Field(default=None)


class DocumentsBaseSchema(CustomModel):
    """Documents Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    currency: str | None = Field(default=None)
    due_date: datetime.date | None = Field(default=None)
    error_message: str | None = Field(default=None)
    file_name: str
    file_size_bytes: int
    file_type: str
    invoice_date: datetime.date | None = Field(default=None)
    invoice_number: str | None = Field(default=None)
    organization_id: UUID4
    status: str | None = Field(default=None)
    storage_path: str
    subtotal: Decimal | None = Field(default=None)
    tax_amount: Decimal | None = Field(default=None)
    total_amount: Decimal | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    uploaded_by: UUID4 | None = Field(default=None)
    vendor_name: str | None = Field(default=None)


class OrganizationsBaseSchema(CustomModel):
    """Organizations Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    name: str
    updated_at: datetime.datetime | None = Field(default=None)


class ProfilesBaseSchema(CustomModel):
    """Profiles Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    role: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


# INSERT CLASSES
# Note: These models are used for insert operations. Auto-generated fields
# (like IDs and timestamps) are optional.


class DocumentLineItemsInsert(CustomModelInsert):
    """DocumentLineItems Insert Schema."""

    # Primary Keys
    # Field properties:
    # created_at: nullable, has default value
    # gl_code: nullable
    # quantity: nullable, has default value
    # unit_price: nullable

    # Required fields
    description: str
    document_id: UUID4
    total_price: Decimal

    # Optional fields
    gl_code: str | None = Field(default=None)
    quantity: int | None = Field(default=None)
    unit_price: Decimal | None = Field(default=None)


class DocumentsInsert(CustomModelInsert):
    """Documents Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # currency: nullable, has default value
    # due_date: nullable
    # error_message: nullable
    # invoice_date: nullable
    # invoice_number: nullable
    # status: nullable, has default value
    # subtotal: nullable
    # tax_amount: nullable
    # total_amount: nullable
    # updated_at: nullable, has default value
    # uploaded_by: nullable
    # vendor_name: nullable

    # Required fields
    file_name: str
    file_size_bytes: int
    file_type: str
    organization_id: UUID4
    storage_path: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    currency: str | None = Field(default=None)
    due_date: datetime.date | None = Field(default=None)
    error_message: str | None = Field(default=None)
    invoice_date: datetime.date | None = Field(default=None)
    invoice_number: str | None = Field(default=None)
    status: str | None = Field(default=None)
    subtotal: Decimal | None = Field(default=None)
    tax_amount: Decimal | None = Field(default=None)
    total_amount: Decimal | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    uploaded_by: UUID4 | None = Field(default=None)
    vendor_name: str | None = Field(default=None)


class OrganizationsInsert(CustomModelInsert):
    """Organizations Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # updated_at: nullable, has default value

    # Required fields
    name: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ProfilesInsert(CustomModelInsert):
    """Profiles Insert Schema."""

    # Primary Keys
    id: UUID4

    # Field properties:
    # created_at: nullable, has default value
    # first_name: nullable
    # last_name: nullable
    # organization_id: nullable
    # role: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    role: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


# UPDATE CLASSES
# Note: These models are used for update operations. All fields are optional.


class DocumentLineItemsUpdate(CustomModelUpdate):
    """DocumentLineItems Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # gl_code: nullable
    # quantity: nullable, has default value
    # unit_price: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    gl_code: str | None = Field(default=None)
    quantity: int | None = Field(default=None)
    total_price: Decimal | None = Field(default=None)
    unit_price: Decimal | None = Field(default=None)


class DocumentsUpdate(CustomModelUpdate):
    """Documents Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # currency: nullable, has default value
    # due_date: nullable
    # error_message: nullable
    # invoice_date: nullable
    # invoice_number: nullable
    # status: nullable, has default value
    # subtotal: nullable
    # tax_amount: nullable
    # total_amount: nullable
    # updated_at: nullable, has default value
    # uploaded_by: nullable
    # vendor_name: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    currency: str | None = Field(default=None)
    due_date: datetime.date | None = Field(default=None)
    error_message: str | None = Field(default=None)
    file_name: str | None = Field(default=None)
    file_size_bytes: int | None = Field(default=None)
    file_type: str | None = Field(default=None)
    invoice_date: datetime.date | None = Field(default=None)
    invoice_number: str | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    status: str | None = Field(default=None)
    storage_path: str | None = Field(default=None)
    subtotal: Decimal | None = Field(default=None)
    tax_amount: Decimal | None = Field(default=None)
    total_amount: Decimal | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    uploaded_by: UUID4 | None = Field(default=None)
    vendor_name: str | None = Field(default=None)


class OrganizationsUpdate(CustomModelUpdate):
    """Organizations Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    name: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ProfilesUpdate(CustomModelUpdate):
    """Profiles Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # first_name: nullable
    # last_name: nullable
    # organization_id: nullable
    # role: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    role: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


# OPERATIONAL CLASSES


class DocumentLineItems(DocumentLineItemsBaseSchema):
    """DocumentLineItems Schema for Pydantic.

    Inherits from DocumentLineItemsBaseSchema. Add any customization here.
    """

    # Foreign Keys
    document: Documents | None = Field(default=None)


class Documents(DocumentsBaseSchema):
    """Documents Schema for Pydantic.

    Inherits from DocumentsBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organization: Organizations | None = Field(default=None)
    profile: Profiles | None = Field(default=None)
    document_line_items: list[DocumentLineItems] | None = Field(default=None)


class Organizations(OrganizationsBaseSchema):
    """Organizations Schema for Pydantic.

    Inherits from OrganizationsBaseSchema. Add any customization here.
    """

    # Foreign Keys
    documents: list[Documents] | None = Field(default=None)
    profiles: list[Profiles] | None = Field(default=None)


class Profiles(ProfilesBaseSchema):
    """Profiles Schema for Pydantic.

    Inherits from ProfilesBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organization: Organizations | None = Field(default=None)
    documents: Documents | None = Field(default=None)
