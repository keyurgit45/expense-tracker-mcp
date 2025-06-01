from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class Category(BaseModel):
    category_id: UUID
    name: str
    is_active: bool = True
    parent_category_id: Optional[UUID] = None


class Transaction(BaseModel):
    transaction_id: UUID
    date: date
    amount: Decimal
    merchant: Optional[str] = None
    category_id: Optional[UUID] = None
    is_recurring: bool = False
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Tag(BaseModel):
    tag_id: UUID
    value: str


class TransactionTag(BaseModel):
    transaction_id: UUID
    tag_id: UUID