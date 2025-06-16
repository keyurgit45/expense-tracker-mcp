#!/usr/bin/env python3
"""
Script to upload default categories to Supabase database
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure we're not in test environment
if os.getenv("ENVIRONMENT") == "test":
    print("❌ Cannot run upload script in test environment!")
    sys.exit(1)

from app.database import supabase
from app.crud import categories
from app.schemas.schemas import CategoryCreate
from scripts.categories_data import DEFAULT_CATEGORIES, FLAT_CATEGORIES


async def check_existing_categories() -> List[str]:
    """Check what categories already exist in the database"""
    try:
        existing = await categories.get_categories(supabase, 0, 1000, active_only=False)
        return [cat.name for cat in existing]
    except Exception as e:
        print(f"Error checking existing categories: {e}")
        return []


async def upload_hierarchical_categories(dry_run: bool = True) -> Dict[str, int]:
    """Upload categories with parent-child relationships"""
    print("📁 Uploading hierarchical categories...")
    
    existing_categories = await check_existing_categories()
    stats = {"created": 0, "skipped": 0, "errors": 0}
    parent_map = {}  # Track parent category IDs
    
    for category_group in DEFAULT_CATEGORIES:
        parent_name = category_group["name"]
        
        # Create parent category
        if parent_name not in existing_categories:
            if not dry_run:
                try:
                    parent_category = await categories.create_category(
                        supabase, 
                        CategoryCreate(name=parent_name, is_active=True)
                    )
                    parent_map[parent_name] = parent_category.category_id
                    stats["created"] += 1
                    print(f"✓ Created parent category: {parent_name}")
                except Exception as e:
                    print(f"❌ Error creating parent category '{parent_name}': {e}")
                    stats["errors"] += 1
                    continue
            else:
                print(f"[DRY RUN] Would create parent category: {parent_name}")
                stats["created"] += 1
        else:
            print(f"⏭ Skipped existing parent category: {parent_name}")
            stats["skipped"] += 1
            # In real run, get existing parent ID
            if not dry_run:
                try:
                    existing_parent = await categories.get_category_by_name(supabase, parent_name)
                    if existing_parent:
                        parent_map[parent_name] = existing_parent.category_id
                except Exception as e:
                    print(f"❌ Error getting existing parent '{parent_name}': {e}")
        
        # Create subcategories
        for sub_name in category_group.get("subcategories", []):
            if sub_name not in existing_categories:
                if not dry_run:
                    try:
                        parent_id = parent_map.get(parent_name)
                        await categories.create_category(
                            supabase,
                            CategoryCreate(
                                name=sub_name, 
                                is_active=True,
                                parent_category_id=parent_id
                            )
                        )
                        stats["created"] += 1
                        print(f"  ✓ Created subcategory: {sub_name}")
                    except Exception as e:
                        print(f"  ❌ Error creating subcategory '{sub_name}': {e}")
                        stats["errors"] += 1
                else:
                    print(f"  [DRY RUN] Would create subcategory: {sub_name}")
                    stats["created"] += 1
            else:
                print(f"  ⏭ Skipped existing subcategory: {sub_name}")
                stats["skipped"] += 1
    
    return stats


async def upload_flat_categories(dry_run: bool = True) -> Dict[str, int]:
    """Upload categories without parent-child relationships"""
    print("📋 Uploading flat categories...")
    
    existing_categories = await check_existing_categories()
    stats = {"created": 0, "skipped": 0, "errors": 0}
    
    for category_name in FLAT_CATEGORIES:
        if category_name not in existing_categories:
            if not dry_run:
                try:
                    await categories.create_category(
                        supabase,
                        CategoryCreate(name=category_name, is_active=True)
                    )
                    stats["created"] += 1
                    print(f"✓ Created category: {category_name}")
                except Exception as e:
                    print(f"❌ Error creating category '{category_name}': {e}")
                    stats["errors"] += 1
            else:
                print(f"[DRY RUN] Would create category: {category_name}")
                stats["created"] += 1
        else:
            print(f"⏭ Skipped existing category: {category_name}")
            stats["skipped"] += 1
    
    return stats


async def main():
    """Main script execution"""
    print("🏷 Expense Categories Upload Script")
    print("=" * 50)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Upload categories to Supabase")
    parser.add_argument("--structure", choices=["flat", "hierarchical"], default="hierarchical",
                       help="Category structure to upload (default: hierarchical)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be created without making changes")
    parser.add_argument("--force", action="store_true",
                       help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    # Safety check
    try:
        from app.config import get_settings
        settings = get_settings()
        if settings.environment == "test":
            print("❌ Cannot run in test environment!")
            sys.exit(1)
        
        print(f"📍 Environment: {settings.environment}")
        print(f"🗄 Database: {settings.effective_supabase_url[:50]}...")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Confirmation
    if not args.force and not args.dry_run:
        print(f"\n⚠️  You are about to upload categories to the {settings.environment} database.")
        response = input("Continue? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Cancelled by user")
            sys.exit(0)
    
    try:
        # Check database connection
        existing_count = len(await check_existing_categories())
        print(f"📊 Found {existing_count} existing categories")
        
        # Upload based on structure choice
        if args.structure == "hierarchical":
            stats = await upload_hierarchical_categories(dry_run=args.dry_run)
        else:
            stats = await upload_flat_categories(dry_run=args.dry_run)
        
        # Summary
        print("\n" + "=" * 50)
        print("📈 Upload Summary:")
        print(f"✅ Created: {stats['created']}")
        print(f"⏭ Skipped: {stats['skipped']}")
        print(f"❌ Errors: {stats['errors']}")
        
        if args.dry_run:
            print("\n🔍 This was a dry run - no changes were made")
            print("Run without --dry-run to actually upload categories")
        else:
            print(f"\n🎉 Successfully uploaded categories to {settings.environment} database!")
            
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())