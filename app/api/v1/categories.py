from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.database import supabase
from app.schemas.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.crud import categories

router = APIRouter()


@router.post("/", response_model=CategoryResponse)
async def create_category(category: CategoryCreate):
    try:
        return await categories.create_category(supabase, category)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    category = await categories.get_category(supabase, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True)
):
    return await categories.get_categories(supabase, skip, limit, active_only)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, category_update: CategoryUpdate):
    category = await categories.update_category(supabase, category_id, category_update)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/{category_id}")
async def delete_category(category_id: str):
    success = await categories.delete_category(supabase, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


@router.get("/tree")
async def get_categories_tree(active_only: bool = Query(True)):
    """Get categories in a hierarchical tree structure"""
    # Get all categories
    all_categories = await categories.get_categories(supabase, 0, 1000, active_only)
    
    # Build tree manually
    tree = []
    
    for cat in all_categories:
        if not cat.parent_category_id:  # This is a parent category
            parent_dict = {
                "category_id": str(cat.category_id),
                "name": cat.name,
                "is_active": cat.is_active,
                "parent_category_id": None,
                "children": []
            }
            
            # Find children
            for child_cat in all_categories:
                if str(child_cat.parent_category_id) == str(cat.category_id):
                    child_dict = {
                        "category_id": str(child_cat.category_id),
                        "name": child_cat.name,
                        "is_active": child_cat.is_active,
                        "parent_category_id": str(child_cat.parent_category_id),
                        "children": []
                    }
                    parent_dict["children"].append(child_dict)
            
            tree.append(parent_dict)
    
    return tree