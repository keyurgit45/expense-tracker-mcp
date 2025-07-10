from typing import List, Optional
import uuid
from app.core.repositories.tag_repository import TagRepository
from app.core.models.models import TagCreate, TagResponse, TransactionTagCreate


class TagService:
    def __init__(self, tag_repo: TagRepository):
        self.tag_repo = tag_repo

    async def create_tag(self, tag_data: TagCreate) -> TagResponse:
        """Create a new tag"""
        # Check if tag already exists
        existing = await self.tag_repo.get_tag_by_value(tag_data.value)
        if existing:
            raise ValueError(f"Tag with value '{tag_data.value}' already exists")
        
        return await self.tag_repo.create_tag(tag_data)

    async def get_tag(self, tag_id: str) -> Optional[TagResponse]:
        """Get a single tag by ID"""
        return await self.tag_repo.get_tag(tag_id)

    async def get_tag_by_value(self, value: str) -> Optional[TagResponse]:
        """Get a tag by its value"""
        return await self.tag_repo.get_tag_by_value(value)

    async def get_tags(self, skip: int = 0, limit: int = 100) -> List[TagResponse]:
        """Get a list of tags"""
        return await self.tag_repo.get_tags(skip, limit)

    async def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag and all its associations"""
        return await self.tag_repo.delete_tag(tag_id)

    async def add_tag_to_transaction(self, transaction_id: str, tag_id: str) -> bool:
        """Add a tag to a transaction"""
        # Verify tag exists
        tag = await self.tag_repo.get_tag(tag_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found")
        
        transaction_tag = TransactionTagCreate(
            transaction_id=uuid.UUID(transaction_id),
            tag_id=uuid.UUID(tag_id)
        )
        return await self.tag_repo.add_tag_to_transaction(transaction_tag)

    async def remove_tag_from_transaction(self, transaction_id: str, tag_id: str) -> bool:
        """Remove a tag from a transaction"""
        return await self.tag_repo.remove_tag_from_transaction(transaction_id, tag_id)

    async def get_transaction_tags(self, transaction_id: str) -> List[TagResponse]:
        """Get all tags for a transaction"""
        return await self.tag_repo.get_transaction_tags(transaction_id)

    async def get_or_create_tag(self, value: str) -> TagResponse:
        """Get an existing tag or create it if it doesn't exist"""
        existing = await self.tag_repo.get_tag_by_value(value)
        if existing:
            return existing
        
        tag_data = TagCreate(value=value)
        return await self.tag_repo.create_tag(tag_data)