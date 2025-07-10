from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from app.core.repositories.transaction_repository import TransactionRepository
from app.core.repositories.category_repository import CategoryRepository
from app.core.repositories.tag_repository import TagRepository
from app.core.models.models import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionWithTags, TransactionTagCreate


class TransactionService:
    def __init__(self, transaction_repo: TransactionRepository, category_repo: CategoryRepository, tag_repo: TagRepository):
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo
        self.tag_repo = tag_repo

    async def create_expense(self, transaction_data: TransactionCreate) -> TransactionResponse:
        """Create a new expense transaction"""
        # If category_id is provided, verify it exists
        if transaction_data.category_id:
            category = await self.category_repo.get_category(str(transaction_data.category_id))
            if not category:
                raise ValueError(f"Category {transaction_data.category_id} not found")
        
        # Create the transaction
        return await self.transaction_repo.create_transaction(transaction_data)

    async def get_transaction(self, transaction_id: str) -> Optional[TransactionResponse]:
        """Get a single transaction by ID"""
        return await self.transaction_repo.get_transaction(transaction_id)

    async def get_transaction_with_tags(self, transaction_id: str) -> Optional[TransactionWithTags]:
        """Get a transaction with its associated tags"""
        return await self.transaction_repo.get_transaction_with_tags(transaction_id)

    async def get_transactions(self, skip: int = 0, limit: int = 100, category_id: Optional[str] = None) -> List[TransactionResponse]:
        """Get a list of transactions"""
        return await self.transaction_repo.get_transactions(skip, limit, category_id)

    async def update_transaction(self, transaction_id: str, transaction_update: TransactionUpdate) -> Optional[TransactionResponse]:
        """Update an existing transaction"""
        # If category_id is being updated, verify it exists
        if transaction_update.category_id:
            category = await self.category_repo.get_category(str(transaction_update.category_id))
            if not category:
                raise ValueError(f"Category {transaction_update.category_id} not found")
        
        return await self.transaction_repo.update_transaction(transaction_id, transaction_update)

    async def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction"""
        return await self.transaction_repo.delete_transaction(transaction_id)

    async def get_spending_summary(self, period: str = "month", category_id: Optional[str] = None) -> dict:
        """Get spending summary for a period"""
        # Determine date range based on period
        end_date = datetime.now()
        if period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # Default to month

        # Get transactions in date range
        transactions = await self.transaction_repo.get_transactions(skip=0, limit=1000, category_id=category_id)
        
        # Get all unique category IDs
        category_ids = set()
        for transaction in transactions:
            if transaction.category_id and start_date <= transaction.date <= end_date:
                category_ids.add(str(transaction.category_id))
        
        # Fetch all categories at once
        category_map = {}
        for cat_id in category_ids:
            category = await self.category_repo.get_category(cat_id)
            if category:
                category_map[cat_id] = category.name
        
        # Filter by date and calculate summary
        total = Decimal(0)
        count = 0
        category_totals = {}
        
        for transaction in transactions:
            if start_date <= transaction.date <= end_date:
                total += transaction.amount
                count += 1
                
                if transaction.category_id:
                    cat_id_str = str(transaction.category_id)
                    if cat_id_str in category_map:
                        category_name = category_map[cat_id_str]
                        if category_name not in category_totals:
                            category_totals[category_name] = Decimal(0)
                        category_totals[category_name] += transaction.amount

        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_spent": float(total),
            "transaction_count": count,
            "average_transaction": float(total / count) if count > 0 else 0,
            "category_breakdown": {k: float(v) for k, v in category_totals.items()}
        }

    async def add_tags_to_transaction(self, transaction_id: str, tag_ids: List[str]) -> TransactionWithTags:
        """Add tags to a transaction"""
        # Verify transaction exists
        transaction = await self.transaction_repo.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        # Add each tag
        for tag_id in tag_ids:
            tag = await self.tag_repo.get_tag(tag_id)
            if tag:
                await self.tag_repo.add_tag_to_transaction(
                    TransactionTagCreate(
                        transaction_id=uuid.UUID(transaction_id),
                        tag_id=uuid.UUID(tag_id)
                    )
                )
        
        return await self.transaction_repo.get_transaction_with_tags(transaction_id)