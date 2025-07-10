import uuid
from typing import List, Optional
from datetime import datetime, timezone
from supabase import Client
from app.core.models.models import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionWithTags, TagResponse


class TransactionRepository:
    def __init__(self, db: Client):
        self.db = db

    async def create_transaction(self, transaction: TransactionCreate) -> TransactionResponse:
        transaction_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Ensure transaction date has timezone info
        transaction_date = transaction.date
        if transaction_date.tzinfo is None:
            transaction_date = transaction_date.replace(tzinfo=timezone.utc)
        
        data = {
            "transaction_id": transaction_id,
            "date": transaction_date.isoformat(),
            "amount": float(transaction.amount),
            "merchant": transaction.merchant,
            "category_id": str(transaction.category_id) if transaction.category_id else None,
            "is_recurring": transaction.is_recurring,
            "notes": transaction.notes,
            "created_at": now,
            "updated_at": now
        }
        
        result = self.db.table("transactions").insert(data).execute()
        return TransactionResponse(**result.data[0])


    async def get_transaction(self, transaction_id: str) -> Optional[TransactionResponse]:
        result = self.db.table("transactions").select("*").eq("transaction_id", transaction_id).execute()
        if result.data:
            return TransactionResponse(**result.data[0])
        return None


    async def get_transactions(self, skip: int = 0, limit: int = 100, category_id: Optional[str] = None) -> List[TransactionResponse]:
        query = self.db.table("transactions").select("*")
        if category_id:
            query = query.eq("category_id", category_id)
        
        result = query.order("date", desc=True).range(skip, skip + limit - 1).execute()
        return [TransactionResponse(**item) for item in result.data]


    async def get_transaction_with_tags(self, transaction_id: str) -> Optional[TransactionWithTags]:
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            return None
        
        tags_result = self.db.table("transaction_tags").select(
            "tags(tag_id, value)"
        ).eq("transaction_id", transaction_id).execute()
        
        tags = []
        for item in tags_result.data:
            if item.get("tags"):
                tags.append(TagResponse(**item["tags"]))
        
        return TransactionWithTags(**transaction.dict(), tags=tags)


    async def update_transaction(self, transaction_id: str, transaction_update: TransactionUpdate) -> Optional[TransactionResponse]:
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if transaction_update.date is not None:
            transaction_date = transaction_update.date
            if transaction_date.tzinfo is None:
                transaction_date = transaction_date.replace(tzinfo=timezone.utc)
            update_data["date"] = transaction_date.isoformat()
        if transaction_update.amount is not None:
            update_data["amount"] = float(transaction_update.amount)
        if transaction_update.merchant is not None:
            update_data["merchant"] = transaction_update.merchant
        if transaction_update.category_id is not None:
            update_data["category_id"] = str(transaction_update.category_id)
        if transaction_update.is_recurring is not None:
            update_data["is_recurring"] = transaction_update.is_recurring
        if transaction_update.notes is not None:
            update_data["notes"] = transaction_update.notes
        
        result = self.db.table("transactions").update(update_data).eq("transaction_id", transaction_id).execute()
        if result.data:
            return TransactionResponse(**result.data[0])
        return None


    async def delete_transaction(self, transaction_id: str) -> bool:
        result = self.db.table("transactions").delete().eq("transaction_id", transaction_id).execute()
        return len(result.data) > 0