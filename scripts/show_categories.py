#!/usr/bin/env python3
import asyncio
import httpx
import os
from typing import Dict, List


def check_environment():
    """Ensure we're not running against production accidentally"""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        print("⚠️  WARNING: Running against production database (read-only)")
    
    print(f"📖 Environment: {env} (read-only operation)")


async def show_all_categories(base_url: str = "http://localhost:8000"):
    """Display all categories in a hierarchical tree structure"""
    check_environment()
    
    async with httpx.AsyncClient() as client:
        try:
            print("🗂️  EXPENSE TRACKER CATEGORIES")
            print("=" * 60)
            
            # Get all categories
            response = await client.get(f"{base_url}/api/v1/categories/")
            if response.status_code != 200:
                print(f"❌ Error fetching categories: {response.status_code}")
                return
                
            categories = response.json()
            
            # Separate parents and children
            parents = [c for c in categories if c['parent_category_id'] is None]
            children = [c for c in categories if c['parent_category_id'] is not None]
            
            # Sort parents alphabetically
            parents.sort(key=lambda x: x['name'])
            
            print(f"📊 Total: {len(parents)} parent categories, {len(children)} subcategories\n")
            
            # Display each parent with its children
            for i, parent in enumerate(parents, 1):
                # Color coding for expense vs income categories
                if any(keyword in parent['name'].lower() for keyword in ['income', 'salary', 'dividend', 'passive']):
                    icon = "💰"  # Income categories
                else:
                    icon = "💸"  # Expense categories
                
                print(f"{icon} {i:2d}. {parent['name']}")
                print(f"    {'─' * (len(parent['name']) + 4)}")
                
                # Find and display children for this parent
                parent_children = [c for c in children if c['parent_category_id'] == parent['category_id']]
                parent_children.sort(key=lambda x: x['name'])
                
                for j, child in enumerate(parent_children, 1):
                    prefix = "└──" if j == len(parent_children) else "├──"
                    print(f"    {prefix} {child['name']}")
                
                if not parent_children:
                    print("    └── (No subcategories)")
                
                print()  # Empty line between categories
            
            print("=" * 60)
            print(f"✅ Displayed {len(parents)} parent categories with {len(children)} total subcategories")
            
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(show_all_categories())