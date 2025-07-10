"""
MCP Tools for Expense Tracker
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from mcp.server.fastmcp import FastMCP
from app.core.database.connection import supabase
from app.core.repositories.category_repository import CategoryRepository
from app.core.repositories.transaction_repository import TransactionRepository
from app.core.repositories.tag_repository import TagRepository
from app.core.services.category_service import CategoryService
from app.core.services.transaction_service import TransactionService
from app.core.services.tag_service import TagService
from app.core.services.categorization_service import CategorizationService
from app.core.models.models import TransactionCreate, TransactionUpdate, TransactionTagCreate
from app.servers.mcp.tags_config import validate_tags, VALID_TAGS

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_services():
    """Get service instances"""
    # Initialize repositories
    category_repo = CategoryRepository(supabase)
    transaction_repo = TransactionRepository(supabase)
    tag_repo = TagRepository(supabase)
    
    # Initialize services
    category_service = CategoryService(category_repo)
    transaction_service = TransactionService(transaction_repo, category_repo, tag_repo)
    tag_service = TagService(tag_repo)
    categorization_service = CategorizationService(supabase, category_repo)
    
    return {
        "category": category_service,
        "transaction": transaction_service,
        "tag": tag_service,
        "categorization": categorization_service
    }


def register_tools(mcp: FastMCP):
    """Register all MCP tools"""
    
    @mcp.tool()
    async def create_expense(
        amount: float,
        merchant: str,
        date: Optional[str] = None,
        category_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_recurring: bool = False
    ) -> dict:
        """
        Create a new expense transaction with optional automatic categorization.
        
        Args:
            amount: Transaction amount (use negative for expenses, positive for income)
            merchant: Merchant/vendor name
            date: Transaction date in ISO format (defaults to today)
            category_name: Category name (if not provided, will auto-categorize)
            description: Optional description or notes
            tags: List of tags from predefined set
            is_recurring: Whether this is a recurring transaction
            
        Returns:
            Created transaction with category and tags
        """
        services = get_services()
        
        try:
            # Parse date
            if date:
                transaction_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            else:
                transaction_date = datetime.now(timezone.utc)
            
            # Validate tags if provided
            if tags:
                valid, invalid = validate_tags(tags)
                if not valid:
                    return {
                        "error": f"Invalid tags: {invalid}. Valid tags are: {VALID_TAGS}"
                    }
            
            # Find or auto-categorize
            category_id = None
            if category_name:
                categories = await services["category"].get_categories(0, 1000)
                for cat in categories:
                    if cat.name.lower() == category_name.lower():
                        category_id = cat.category_id
                        break
                if not category_id:
                    return {"error": f"Category '{category_name}' not found"}
            
            # Create transaction
            transaction_data = TransactionCreate(
                date=transaction_date,
                amount=Decimal(str(abs(amount))),  # Store as positive
                merchant=merchant,
                category_id=category_id,
                is_recurring=is_recurring,
                notes=description
            )
            
            transaction = await services["transaction"].create_expense(transaction_data)
            
            # Auto-categorize if no category provided
            if not category_id:
                cat_id, cat_name, confidence = await services["categorization"].categorize_transaction(
                    transaction, description
                )
                if cat_id:
                    # Update transaction with category
                    update_data = TransactionUpdate(category_id=cat_id)
                    transaction = await services["transaction"].update_transaction(
                        str(transaction.transaction_id), update_data
                    )
                    
                    # Store embedding for learning
                    transaction_text = services["categorization"].embedding_service.format_transaction_text(
                        date=transaction.date,
                        amount=transaction.amount,
                        merchant=transaction.merchant,
                        description=description,
                        category=cat_name
                    )
                    await services["categorization"].store_transaction_embedding(
                        transaction_id=transaction.transaction_id,
                        transaction_text=transaction_text,
                        category_id=cat_id,
                        category_name=cat_name,
                        confidence_score=confidence
                    )
            
            # Add tags if provided
            if tags:
                for tag_value in tags:
                    tag = await services["tag"].get_or_create_tag(tag_value)
                    await services["tag"].add_tag_to_transaction(
                        str(transaction.transaction_id), str(tag.tag_id)
                    )
            
            # Get final transaction with tags
            final_transaction = await services["transaction"].get_transaction_with_tags(
                str(transaction.transaction_id)
            )
            
            return {
                "transaction_id": str(final_transaction.transaction_id),
                "date": final_transaction.date.isoformat(),
                "amount": float(final_transaction.amount) * (-1 if amount < 0 else 1),
                "merchant": final_transaction.merchant,
                "category": await _get_category_name(final_transaction.category_id, services["category"]),
                "tags": [tag.value for tag in final_transaction.tags],
                "is_recurring": final_transaction.is_recurring,
                "notes": final_transaction.notes
            }
            
        except Exception as e:
            logger.error(f"Error creating expense: {str(e)}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def get_spending_summary(period: str = "month", category_name: Optional[str] = None) -> dict:
        """
        Get spending summary and insights for a time period.
        
        Args:
            period: Time period ('week', 'month', 'year')
            category_name: Optional category filter
            
        Returns:
            Spending summary with totals and insights
        """
        services = get_services()
        
        try:
            # Find category if specified
            category_id = None
            if category_name:
                categories = await services["category"].get_categories(0, 1000)
                for cat in categories:
                    if cat.name.lower() == category_name.lower():
                        category_id = str(cat.category_id)
                        break
            
            summary = await services["transaction"].get_spending_summary(period, category_id)
            
            # Generate insights
            insights = []
            if summary["transaction_count"] > 0:
                avg_transaction = summary["average_transaction"]
                insights.append(f"Average transaction: ₹{avg_transaction:.2f}")
                
                if summary["category_breakdown"]:
                    top_category = max(summary["category_breakdown"].items(), key=lambda x: x[1])
                    insights.append(f"Top spending category: {top_category[0]} (₹{top_category[1]:.2f})")
            
            summary["insights"] = insights
            return summary
            
        except Exception as e:
            logger.error(f"Error getting spending summary: {str(e)}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def get_available_categories() -> dict:
        """
        Get all available expense categories in a hierarchical structure.
        
        Returns:
            Hierarchical list of categories
        """
        services = get_services()
        
        try:
            hierarchy = await services["category"].get_category_hierarchy()
            return {"categories": hierarchy}
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return {"error": str(e)}
    
    
    @mcp.tool()
    async def get_recent_transactions(limit: int = 10) -> dict:
        """
        Get recent transactions.
        
        Args:
            limit: Number of transactions to return (max 100)
            
        Returns:
            List of recent transactions
        """
        services = get_services()
        
        try:
            limit = min(limit, 100)
            transactions = await services["transaction"].get_transactions(0, limit)
            
            result = []
            for tx in transactions:
                category_name = await _get_category_name(tx.category_id, services["category"])
                tags = await services["tag"].get_transaction_tags(str(tx.transaction_id))
                
                result.append({
                    "transaction_id": str(tx.transaction_id),
                    "date": tx.date.isoformat(),
                    "amount": float(tx.amount) * -1,  # Show as negative for expenses
                    "merchant": tx.merchant,
                    "category": category_name,
                    "tags": [tag.value for tag in tags],
                    "is_recurring": tx.is_recurring,
                    "notes": tx.notes
                })
            
            return {"transactions": result}
            
        except Exception as e:
            logger.error(f"Error getting recent transactions: {str(e)}")
            return {"error": str(e)}


async def _get_category_name(category_id: Optional[uuid.UUID], category_service: CategoryService) -> Optional[str]:
    """Helper to get category name from ID"""
    if not category_id:
        return None
    category = await category_service.get_category(str(category_id))
    return category.name if category else None