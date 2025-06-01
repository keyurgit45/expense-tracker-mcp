from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.database import supabase
from app.schemas.schemas import TagCreate, TagResponse, TransactionTagCreate
from app.crud import tags

router = APIRouter()


@router.post("/", response_model=TagResponse)
async def create_tag(tag: TagCreate):
    try:
        existing_tag = await tags.get_tag_by_value(supabase, tag.value)
        if existing_tag:
            raise HTTPException(status_code=400, detail="Tag with this value already exists")
        return await tags.create_tag(supabase, tag)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: str):
    tag = await tags.get_tag(supabase, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.get("/", response_model=List[TagResponse])
async def get_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    return await tags.get_tags(supabase, skip, limit)


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str):
    success = await tags.delete_tag(supabase, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag deleted successfully"}


@router.post("/transaction-tags/", response_model=dict)
async def add_tag_to_transaction(transaction_tag: TransactionTagCreate):
    try:
        success = await tags.add_tag_to_transaction(supabase, transaction_tag)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add tag to transaction")
        return {"message": "Tag added to transaction successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/transaction-tags/{transaction_id}/{tag_id}")
async def remove_tag_from_transaction(transaction_id: str, tag_id: str):
    success = await tags.remove_tag_from_transaction(supabase, transaction_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction-tag relationship not found")
    return {"message": "Tag removed from transaction successfully"}


@router.get("/transaction-tags/{transaction_id}", response_model=List[TagResponse])
async def get_transaction_tags(transaction_id: str):
    return await tags.get_transaction_tags(supabase, transaction_id)