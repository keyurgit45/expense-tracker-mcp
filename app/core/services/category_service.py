from typing import List, Optional
from app.core.repositories.category_repository import CategoryRepository
from app.core.models.models import CategoryCreate, CategoryUpdate, CategoryResponse


class CategoryService:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    async def create_category(self, category_data: CategoryCreate) -> CategoryResponse:
        """Create a new category"""
        # Check if category name already exists
        existing = await self.category_repo.get_category_by_name(category_data.name)
        if existing:
            raise ValueError(f"Category with name '{category_data.name}' already exists")
        
        # If parent_category_id is provided, verify it exists
        if category_data.parent_category_id:
            parent = await self.category_repo.get_category(str(category_data.parent_category_id))
            if not parent:
                raise ValueError(f"Parent category {category_data.parent_category_id} not found")
        
        return await self.category_repo.create_category(category_data)

    async def get_category(self, category_id: str) -> Optional[CategoryResponse]:
        """Get a single category by ID"""
        return await self.category_repo.get_category(category_id)

    async def get_categories(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[CategoryResponse]:
        """Get a list of categories"""
        return await self.category_repo.get_categories(skip, limit, active_only)

    async def update_category(self, category_id: str, category_update: CategoryUpdate) -> Optional[CategoryResponse]:
        """Update an existing category"""
        # Verify category exists
        existing = await self.category_repo.get_category(category_id)
        if not existing:
            return None
        
        # If updating name, check for duplicates
        if category_update.name and category_update.name != existing.name:
            duplicate = await self.category_repo.get_category_by_name(category_update.name)
            if duplicate:
                raise ValueError(f"Category with name '{category_update.name}' already exists")
        
        # If updating parent_category_id, verify it exists
        if category_update.parent_category_id:
            parent = await self.category_repo.get_category(str(category_update.parent_category_id))
            if not parent:
                raise ValueError(f"Parent category {category_update.parent_category_id} not found")
        
        return await self.category_repo.update_category(category_id, category_update)

    async def delete_category(self, category_id: str) -> bool:
        """Soft delete a category (set is_active to False)"""
        return await self.category_repo.delete_category(category_id)

    async def get_category_hierarchy(self) -> List[dict]:
        """Get categories organized in a hierarchical structure"""
        all_categories = await self.category_repo.get_categories(skip=0, limit=1000, active_only=True)
        
        # Build hierarchy
        category_map = {str(cat.category_id): cat for cat in all_categories}
        hierarchy = []
        
        for category in all_categories:
            if category.parent_category_id is None:
                # Root category
                cat_dict = {
                    "category_id": str(category.category_id),
                    "name": category.name,
                    "children": []
                }
                # Find children
                for child in all_categories:
                    if child.parent_category_id == category.category_id:
                        cat_dict["children"].append({
                            "category_id": str(child.category_id),
                            "name": child.name
                        })
                hierarchy.append(cat_dict)
        
        return hierarchy