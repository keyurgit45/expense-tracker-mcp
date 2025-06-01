#!/usr/bin/env python3
import asyncio
import httpx
import os
from typing import Dict, List


def check_environment():
    """Ensure we're not running against production accidentally"""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        raise Exception("🚫 SAFETY CHECK: This script should not run against production database!")
    
    supabase_url = os.getenv("SUPABASE_URL", "")
    if "prod" in supabase_url.lower() or "production" in supabase_url.lower():
        raise Exception("🚫 SAFETY CHECK: Detected production URL in environment!")
    
    print(f"✅ Environment check passed: {env}")


CATEGORY_STRUCTURE = {
    # Debit Categories (Expenses)
    "Food & Dining": [
        "Groceries",
        "Restaurants & Takeout", 
        "Coffee & Beverages"
    ],
    "Housing & Utilities": [
        "Rent/Mortgage",
        "Electricity",
        "Water",
        "Gas",
        "Internet",
        "Mobile Recharge",
        "Home Maintenance",
        "HOA Fees"
    ],
    "Transportation": [
        "Fuel",
        "Public Transportation",
        "Vehicle Maintenance & Repairs"
    ],
    "Healthcare": [
        "Doctor Visits",
        "Medications",
        "Other Treatments"
    ],
    "Insurance": [
        "Health Insurance",
        "Vehicle Insurance",
        "Property Insurance",
        "Life Insurance",
        "Pet Insurance",
        "Travel Insurance"
    ],
    "Debt Payments": [
        "Credit Card Payments",
        "Student Loan Repayments",
        "Personal Loan Repayments",
        "Other Loan Repayments"
    ],
    "Entertainment & Subscriptions": [
        "Media (Movies, Streaming Services, Music)",
        "Events (Concerts, Sports, Other)",
        "Subscriptions & Memberships (Magazines, Clubs, Software)"
    ],
    "Personal Care & Fitness": [
        "Grooming (Haircuts, Salon, Spa)",
        "Fitness (Gym Membership, Sports Activities)"
    ],
    "Shopping & Supplies": [
        "Clothing & Accessories",
        "Electronics & Gadgets",
        "Household Items & Home Goods",
        "Office/School Supplies"
    ],
    "Education & Professional": [
        "Tuition & School Fees",
        "Courses & Certifications",
        "Books & Study Materials"
    ],
    "Pets": [
        "Pet Food & Supplies",
        "Veterinary Expenses",
        "Pet Grooming"
    ],
    "Taxes & Fees": [
        "Income Tax Payments",
        "Property Tax",
        "Bank & Credit Card Fees"
    ],
    "Savings & Investments": [
        "Emergency Fund Contributions (Savings Account)",
        "Securities Purchases (Stocks, Mutual Funds)",
        "Retirement Contributions (401(k), PPF, EPF)"
    ],
    "Miscellaneous": [
        "Gifts & Donations (Charitable Contributions, Gifts to Others)",
        "Other Unclassified Expenses"
    ],
    
    # Credit Categories (Income)
    "Primary Income": [
        "Salary",
        "Bonuses"
    ],
    "Secondary Income": [
        "Freelance & Side Projects",
        "Consulting Fees"
    ],
    "Investments & Passive Income": [
        "Dividends",
        "Interest Income (Savings, Bonds)",
        "Rental Income",
        "Royalties"
    ],
    "Other Income": [
        "Tax Refunds",
        "Gifts & Windfalls (Inheritances, One-time Awards)",
        "Reimbursements (Work-related or Expense Refunds)",
        "Grants & Scholarships"
    ]
}


async def populate_hierarchical_categories(base_url: str = "http://localhost:8000"):
    # Safety check before doing anything
    check_environment()
    
    async with httpx.AsyncClient() as client:
        print("Populating hierarchical categories...")
        
        # First, clear existing categories (set them inactive)
        print("Clearing existing categories...")
        try:
            response = await client.get(f"{base_url}/api/v1/categories/")
            if response.status_code == 200:
                existing_categories = response.json()
                for category in existing_categories:
                    await client.delete(f"{base_url}/api/v1/categories/{category['category_id']}")
        except Exception as e:
            print(f"Note: Could not clear existing categories: {e}")
        
        parent_ids = {}
        
        # Create parent categories first
        for parent_name in CATEGORY_STRUCTURE.keys():
            try:
                response = await client.post(
                    f"{base_url}/api/v1/categories/",
                    json={"name": parent_name, "is_active": True}
                )
                if response.status_code == 200:
                    data = response.json()
                    parent_ids[parent_name] = data["category_id"]
                    print(f"✓ Created parent: {parent_name}")
                else:
                    print(f"✗ Failed to create parent: {parent_name} - {response.status_code}")
            except Exception as e:
                print(f"✗ Error creating parent {parent_name}: {e}")
        
        # Create child categories
        for parent_name, children in CATEGORY_STRUCTURE.items():
            if parent_name not in parent_ids:
                print(f"✗ Skipping children for {parent_name} - parent not created")
                continue
                
            parent_id = parent_ids[parent_name]
            
            for child_name in children:
                try:
                    response = await client.post(
                        f"{base_url}/api/v1/categories/",
                        json={
                            "name": child_name,
                            "is_active": True,
                            "parent_category_id": parent_id
                        }
                    )
                    if response.status_code == 200:
                        print(f"  ✓ Created child: {child_name}")
                    else:
                        print(f"  ✗ Failed to create child: {child_name} - {response.status_code}")
                except Exception as e:
                    print(f"  ✗ Error creating child {child_name}: {e}")
        
        # Count totals
        total_parents = len(CATEGORY_STRUCTURE)
        total_children = sum(len(children) for children in CATEGORY_STRUCTURE.values())
        print(f"\nFinished populating {total_parents} parent categories and {total_children} child categories!")


if __name__ == "__main__":
    asyncio.run(populate_hierarchical_categories())