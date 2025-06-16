from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    parent_category_id: Optional[UUID] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    parent_category_id: Optional[UUID] = None


class CategoryResponse(BaseModel):
    category_id: UUID
    name: str
    is_active: bool
    parent_category_id: Optional[UUID] = None




class TransactionCreate(BaseModel):
    date: datetime
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    merchant: Optional[str] = Field(None, max_length=255)
    category_id: Optional[UUID] = None
    is_recurring: bool = False
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    date: Optional[datetime] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    merchant: Optional[str] = Field(None, max_length=255)
    category_id: Optional[UUID] = None
    is_recurring: Optional[bool] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    transaction_id: UUID
    date: datetime
    amount: Decimal
    merchant: Optional[str]
    category_id: Optional[UUID]
    is_recurring: bool
    notes: Optional[str]
    created_at: str
    updated_at: str


class TagCreate(BaseModel):
    value: str = Field(..., min_length=1, max_length=100)


class TagResponse(BaseModel):
    tag_id: UUID
    value: str


class TransactionTagCreate(BaseModel):
    transaction_id: UUID
    tag_id: UUID


class TransactionWithTags(TransactionResponse):
    tags: List[TagResponse] = []