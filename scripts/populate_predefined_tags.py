#!/usr/bin/env python3
"""
Populate predefined tags in the database
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import supabase
from app.crud import tags as tags_crud
from app.schemas.schemas import TagCreate
from app.mcp.tags_config import PREDEFINED_TAGS


async def populate_tags():
    """Populate all predefined tags in the database"""
    print("🏷️  Populating predefined tags...")
    
    created_count = 0
    existing_count = 0
    
    for tag_value, description in PREDEFINED_TAGS.items():
        # Check if tag already exists
        existing_tag = await tags_crud.get_tag_by_value(supabase, tag_value)
        
        if existing_tag:
            print(f"✓ Tag '{tag_value}' already exists")
            existing_count += 1
        else:
            # Create new tag
            try:
                await tags_crud.create_tag(supabase, TagCreate(value=tag_value))
                print(f"✓ Created tag '{tag_value}': {description}")
                created_count += 1
            except Exception as e:
                print(f"✗ Failed to create tag '{tag_value}': {str(e)}")
    
    print(f"\n📊 Summary:")
    print(f"   - Created: {created_count} new tags")
    print(f"   - Existing: {existing_count} tags")
    print(f"   - Total: {len(PREDEFINED_TAGS)} predefined tags")


if __name__ == "__main__":
    asyncio.run(populate_tags())