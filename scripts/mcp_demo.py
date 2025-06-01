#!/usr/bin/env python3
"""
Demo script showing MCP integration for expense tracking
Simulates how an LLM would interact with the MCP tools
"""
import asyncio
import httpx
import json


async def mcp_workflow_demo(base_url: str = "http://localhost:8000"):
    """Demonstrate complete MCP workflow for expense management"""
    async with httpx.AsyncClient() as client:
        print("🤖 MCP EXPENSE TRACKER DEMO")
        print("=" * 50)
        print("Simulating LLM workflow for expense management\n")
        
        # Step 1: Get available categories (what an LLM would do first)
        print("1️⃣ Getting available categories...")
        response = await client.get(f"{base_url}/mcp-tools/categories")
        if response.status_code == 200:
            categories_data = response.json()
            print(f"   📁 Found {categories_data['total_categories']} categories")
            print(f"   📁 Main categories: {len(categories_data['categories'])}")
        
        print()
        
        # Step 2: Auto-categorize some sample transactions
        sample_merchants = [
            {"merchant": "Shell Gas Station", "amount": 45.00},
            {"merchant": "Whole Foods Market", "amount": 127.50},
            {"merchant": "Netflix", "amount": 15.99}
        ]
        
        print("2️⃣ Auto-categorizing sample transactions...")
        categorized_expenses = []
        
        for merchant_data in sample_merchants:
            response = await client.post(
                f"{base_url}/mcp-tools/auto-categorize",
                json=merchant_data
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   🏪 {merchant_data['merchant']} → {result['suggested_category']}")
                categorized_expenses.append({
                    **merchant_data,
                    "category": result["suggested_category"]
                })
        
        print()
        
        # Step 3: Create expenses using MCP tool
        print("3️⃣ Creating expenses via MCP...")
        expense_dates = ["2024-01-25", "2024-01-26", "2024-01-27"]
        
        for i, expense_data in enumerate(categorized_expenses):
            expense_payload = {
                "date": expense_dates[i],
                "amount": expense_data["amount"],
                "merchant": expense_data["merchant"],
                "category": expense_data["category"],
                "notes": f"Auto-created via MCP from {expense_data['merchant']}",
                "tags": ["mcp-demo", "auto-categorized"]
            }
            
            response = await client.post(
                f"{base_url}/mcp-tools/create-expense",
                json=expense_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Created: ${expense_data['amount']} at {expense_data['merchant']}")
                print(f"      ID: {result['transaction_id']}")
            else:
                print(f"   ❌ Failed to create expense: {response.text}")
        
        print()
        
        # Step 4: Get spending summary
        print("4️⃣ Getting spending insights...")
        response = await client.get(f"{base_url}/mcp-tools/spending-summary?days=30")
        if response.status_code == 200:
            summary = response.json()
            print(f"   💰 Total Spending: ${summary['total_amount']:.2f}")
            print(f"   📊 Transaction Count: {summary['transaction_count']}")
            print(f"   🏆 Top Categories:")
            for cat in summary['top_categories'][:3]:
                print(f"      - {cat['category']}: ${cat['amount']:.2f} ({cat['percentage']}%)")
        
        print()
        
        # Step 5: Get recent transactions for context
        print("5️⃣ Recent transactions context...")
        response = await client.get(f"{base_url}/mcp-tools/recent-transactions?limit=5")
        if response.status_code == 200:
            transactions = response.json()
            print(f"   📝 Last {transactions['count']} transactions:")
            for tx in transactions['transactions']:
                print(f"      {tx['date']}: ${tx['amount']:.2f} at {tx['merchant']} ({tx['category']})")
        
        print()
        print("🎉 MCP Workflow Complete!")
        print("=" * 50)
        print("\n📋 Summary of MCP Capabilities:")
        print("✅ Auto-categorization of transactions")
        print("✅ Bulk expense creation from parsed data")
        print("✅ Real-time spending analytics")
        print("✅ Context-aware transaction history")
        print("✅ Hierarchical category management")
        print("\n🚀 This demonstrates how an LLM can:")
        print("   • Parse bank statement PDFs")
        print("   • Auto-categorize each transaction") 
        print("   • Create structured expense records")
        print("   • Provide intelligent spending insights")


if __name__ == "__main__":
    asyncio.run(mcp_workflow_demo())