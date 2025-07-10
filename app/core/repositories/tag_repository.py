import uuid
from typing import List, Optional
from supabase import Client
from app.core.models.models import TagCreate, TagResponse, TransactionTagCreate


class TagRepository:
    def __init__(self, db: Client):
        self.db = db

    async def create_tag(self, tag: TagCreate) -> TagResponse:
        tag_id = str(uuid.uuid4())
        data = {
            "tag_id": tag_id,
            "value": tag.value
        }
        
        result = self.db.table("tags").insert(data).execute()
        return TagResponse(**result.data[0])


    async def get_tag(self, tag_id: str) -> Optional[TagResponse]:
        result = self.db.table("tags").select("*").eq("tag_id", tag_id).execute()
        if result.data:
            return TagResponse(**result.data[0])
        return None


    async def get_tag_by_value(self, value: str) -> Optional[TagResponse]:
        result = self.db.table("tags").select("*").eq("value", value).execute()
        if result.data:
            return TagResponse(**result.data[0])
        return None


    async def get_tags(self, skip: int = 0, limit: int = 100) -> List[TagResponse]:
        result = self.db.table("tags").select("*").range(skip, skip + limit - 1).execute()
        return [TagResponse(**item) for item in result.data]


    async def delete_tag(self, tag_id: str) -> bool:
        self.db.table("transaction_tags").delete().eq("tag_id", tag_id).execute()
        result = self.db.table("tags").delete().eq("tag_id", tag_id).execute()
        return len(result.data) > 0


    async def add_tag_to_transaction(self, transaction_tag: TransactionTagCreate) -> bool:
        data = {
            "transaction_id": str(transaction_tag.transaction_id),
            "tag_id": str(transaction_tag.tag_id)
        }
        
        result = self.db.table("transaction_tags").insert(data).execute()
        return len(result.data) > 0


    async def remove_tag_from_transaction(self, transaction_id: str, tag_id: str) -> bool:
        result = self.db.table("transaction_tags").delete().eq("transaction_id", transaction_id).eq("tag_id", tag_id).execute()
        return len(result.data) > 0


    async def get_transaction_tags(self, transaction_id: str) -> List[TagResponse]:
        result = self.db.table("transaction_tags").select(
            "tags(tag_id, value)"
        ).eq("transaction_id", transaction_id).execute()
        
        tags = []
        for item in result.data:
            if item.get("tags"):
                tags.append(TagResponse(**item["tags"]))
        
        return tags