"""
MCP tools for expense management - designed for LLM integration
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database import supabase
from app.crud import categories, transactions, tags
from app.schemas.schemas import CategoryCreate, TransactionCreate, TagCreate, TransactionTagCreate

# Create dedicated MCP router
mcp_router = APIRouter(prefix="/mcp-tools", tags=["mcp-tools"])


class ExpenseData(BaseModel):
    """Expense data from LLM parsing"""
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    amount: float = Field(..., gt=0, description="Transaction amount (positive number)")
    merchant: str = Field(..., description="Merchant or store name")
    category: Optional[str] = Field(None, description="Category name (will auto-categorize if not provided)")
    notes: Optional[str] = Field(None, description="Additional notes about the transaction")
    tags: List[str] = Field(default=[], description="List of tag values to attach")


class SpendingSummary(BaseModel):
    """Spending summary response"""
    total_amount: float
    transaction_count: int
    top_categories: List[dict]
    date_range: str


@mcp_router.post("/create-expense")
async def create_expense_from_llm(expense: ExpenseData):
    """
    Create a new expense transaction from LLM-parsed bank statement data.
    This is the primary tool for adding expenses from PDF parsing.
    """
    try:
        # Convert date string to date object
        transaction_date = datetime.strptime(expense.date, "%Y-%m-%d").date()
        
        # Find or create category
        category_id = None
        if expense.category:
            # Try to find existing category by name
            existing_category = await categories.get_category_by_name(supabase, expense.category)
            if not existing_category:
                # Create new category if it doesn't exist
                new_category = await categories.create_category(
                    supabase, 
                    CategoryCreate(name=expense.category)
                )
                category_id = new_category.category_id
            else:
                category_id = existing_category.category_id
        
        # Create transaction
        transaction_data = TransactionCreate(
            date=transaction_date,
            amount=Decimal(str(expense.amount)),
            merchant=expense.merchant,
            category_id=category_id,
            notes=expense.notes
        )
        
        new_transaction = await transactions.create_transaction(supabase, transaction_data)
        
        # Add tags if provided
        created_tags = []
        for tag_value in expense.tags:
            # Try to find existing tag
            existing_tag = await tags.get_tag_by_value(supabase, tag_value)
            if not existing_tag:
                # Create new tag
                new_tag = await tags.create_tag(supabase, TagCreate(value=tag_value))
                existing_tag = new_tag
            
            # Link tag to transaction
            await tags.add_tag_to_transaction(
                supabase, 
                TransactionTagCreate(
                    transaction_id=new_transaction.transaction_id,
                    tag_id=existing_tag.tag_id
                )
            )
            created_tags.append(tag_value)
        
        return {
            "success": True,
            "transaction_id": str(new_transaction.transaction_id),
            "message": f"Created expense: ${expense.amount} at {expense.merchant}",
            "category": expense.category,
            "tags": created_tags
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create expense: {str(e)}")


@mcp_router.get("/spending-summary")
async def get_spending_summary(days: int = 30) -> SpendingSummary:
    """
    Get spending summary for LLM analysis and insights.
    Returns total spending, transaction count, and top categories.
    """
    try:
        # Get all transactions (in a real app, you'd filter by date range)
        all_transactions = await transactions.get_transactions(supabase, 0, 1000)
        
        if not all_transactions:
            return SpendingSummary(
                total_amount=0.0,
                transaction_count=0,
                top_categories=[],
                date_range=f"Last {days} days"
            )
        
        # Calculate totals
        total_amount = sum(float(t.amount) for t in all_transactions)
        transaction_count = len(all_transactions)
        
        # Get category breakdown
        category_spending = {}
        for transaction in all_transactions:
            if transaction.category_id:
                category = await categories.get_category(supabase, str(transaction.category_id))
                if category:
                    category_name = category.name
                    category_spending[category_name] = category_spending.get(category_name, 0) + float(transaction.amount)
        
        # Sort categories by spending
        top_categories = [
            {"category": cat, "amount": amount, "percentage": round((amount / total_amount) * 100, 1)}
            for cat, amount in sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return SpendingSummary(
            total_amount=total_amount,
            transaction_count=transaction_count,
            top_categories=top_categories,
            date_range=f"Last {days} days"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get spending summary: {str(e)}")


@mcp_router.get("/categories")
async def get_categories_for_llm():
    """
    Get all available categories for LLM to use in expense categorization.
    Returns hierarchical structure for better AI understanding.
    """
    try:
        all_categories = await categories.get_categories(supabase, 0, 1000, True)
        
        # Organize into hierarchical structure
        parents = [c for c in all_categories if not c.parent_category_id]
        children = [c for c in all_categories if c.parent_category_id]
        
        category_tree = []
        for parent in parents:
            parent_data = {
                "name": parent.name,
                "id": str(parent.category_id),
                "subcategories": []
            }
            
            # Find children
            for child in children:
                if str(child.parent_category_id) == str(parent.category_id):
                    parent_data["subcategories"].append({
                        "name": child.name,
                        "id": str(child.category_id)
                    })
            
            category_tree.append(parent_data)
        
        return {
            "categories": category_tree,
            "total_categories": len(all_categories),
            "message": "Use these categories when creating expenses. Choose the most specific subcategory when possible."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


class CategorizationRequest(BaseModel):
    merchant: str = Field(..., description="Merchant name to categorize")
    amount: Optional[float] = Field(None, description="Transaction amount for context")


@mcp_router.post("/auto-categorize")
async def auto_categorize_transaction(request: CategorizationRequest):
    """
    Auto-categorize a transaction based on merchant name and amount.
    Returns suggested category for LLM to use.
    """
    try:
        # Simple rule-based categorization (could be enhanced with ML)
        merchant_lower = request.merchant.lower()
        
        # Get available categories
        all_categories = await categories.get_categories(supabase, 0, 1000, True)
        category_names = [c.name for c in all_categories]
        
        # Basic categorization rules
        if any(keyword in merchant_lower for keyword in ['grocery', 'supermarket', 'market', 'food']):
            suggested = next((c for c in category_names if 'groceries' in c.lower()), 'Food & Dining')
        elif any(keyword in merchant_lower for keyword in ['gas', 'fuel', 'station', 'shell', 'bp']):
            suggested = next((c for c in category_names if 'fuel' in c.lower()), 'Transportation')
        elif any(keyword in merchant_lower for keyword in ['restaurant', 'cafe', 'pizza', 'burger']):
            suggested = next((c for c in category_names if 'restaurant' in c.lower()), 'Food & Dining')
        elif any(keyword in merchant_lower for keyword in ['amazon', 'target', 'walmart', 'store']):
            suggested = next((c for c in category_names if 'household' in c.lower()), 'Shopping & Supplies')
        else:
            suggested = 'Miscellaneous'
        
        return {
            "merchant": request.merchant,
            "suggested_category": suggested,
            "confidence": "medium",
            "message": f"Suggested category for '{request.merchant}': {suggested}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-categorize: {str(e)}")


@mcp_router.get("/recent-transactions")
async def get_recent_transactions(limit: int = 10):
    """
    Get recent transactions for LLM context and analysis.
    """
    try:
        recent_transactions = await transactions.get_transactions(supabase, 0, limit)
        
        formatted_transactions = []
        for t in recent_transactions:
            # Get category name if available
            category_name = "Uncategorized"
            if t.category_id:
                category = await categories.get_category(supabase, str(t.category_id))
                if category:
                    category_name = category.name
            
            formatted_transactions.append({
                "date": str(t.date),
                "amount": float(t.amount),
                "merchant": t.merchant,
                "category": category_name,
                "notes": t.notes
            })
        
        return {
            "transactions": formatted_transactions,
            "count": len(formatted_transactions),
            "message": f"Last {len(formatted_transactions)} transactions"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent transactions: {str(e)}")