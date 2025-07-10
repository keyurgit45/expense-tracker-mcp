import uuid
from typing import List, Optional
from supabase import Client
from app.core.models.models import CategoryCreate, CategoryUpdate, CategoryResponse


class CategoryRepository:
    def __init__(self, db: Client):
        self.db = db

    async def create_category(self, category: CategoryCreate) -> CategoryResponse:
        category_id = str(uuid.uuid4())
        data = {
            "category_id": category_id,
            "name": category.name,
            "is_active": category.is_active,
            "parent_category_id": str(category.parent_category_id) if category.parent_category_id else None
        }
        
        result = self.db.table("categories").insert(data).execute()
        return CategoryResponse(**result.data[0])


    async def get_category(self, category_id: str) -> Optional[CategoryResponse]:
        result = self.db.table("categories").select("*").eq("category_id", category_id).execute()
        if result.data:
            return CategoryResponse(**result.data[0])
        return None


    async def get_categories(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[CategoryResponse]:
        query = self.db.table("categories").select("*")
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.range(skip, skip + limit - 1).execute()
        return [CategoryResponse(**item) for item in result.data]


    async def update_category(self, category_id: str, category_update: CategoryUpdate) -> Optional[CategoryResponse]:
        update_data = {}
        if category_update.name is not None:
            update_data["name"] = category_update.name
        if category_update.is_active is not None:
            update_data["is_active"] = category_update.is_active
        if category_update.parent_category_id is not None:
            update_data["parent_category_id"] = str(category_update.parent_category_id)
        
        if not update_data:
            return await self.get_category(category_id)
        
        result = self.db.table("categories").update(update_data).eq("category_id", category_id).execute()
        if result.data:
            return CategoryResponse(**result.data[0])
        return None


    async def delete_category(self, category_id: str) -> bool:
        result = self.db.table("categories").update({"is_active": False}).eq("category_id", category_id).execute()
        return len(result.data) > 0




    async def get_category_by_name(self, name: str) -> Optional[CategoryResponse]:
        result = self.db.table("categories").select("*").eq("name", name).execute()
        if result.data:
            return CategoryResponse(**result.data[0])
        return None