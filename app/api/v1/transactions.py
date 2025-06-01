from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.database import supabase
from app.schemas.schemas import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionWithTags
from app.crud import transactions

router = APIRouter()


@router.post("/", response_model=TransactionResponse)
async def create_transaction(transaction: TransactionCreate):
    try:
        return await transactions.create_transaction(supabase, transaction)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    transaction = await transactions.get_transaction(supabase, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.get("/{transaction_id}/with-tags", response_model=TransactionWithTags)
async def get_transaction_with_tags(transaction_id: str):
    transaction = await transactions.get_transaction_with_tags(supabase, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[str] = Query(None)
):
    return await transactions.get_transactions(supabase, skip, limit, category_id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(transaction_id: str, transaction_update: TransactionUpdate):
    transaction = await transactions.update_transaction(supabase, transaction_id, transaction_update)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: str):
    success = await transactions.delete_transaction(supabase, transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}