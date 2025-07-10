"""
MCP Resources for Expense Tracker - Resource providers
"""
from mcp.server.fastmcp import FastMCP
from app.servers.mcp.tags_config import PREDEFINED_TAGS


def register_resources(mcp: FastMCP):
    """Register all MCP resources with the server"""
    
    @mcp.resource("expense-tracker://recent-transactions")
    async def recent_transactions_resource() -> str:
        """Resource providing recent transactions for context"""
        try:
            # Import here to avoid circular imports
            from app.core.database.connection import supabase
            from app.core.repositories.transaction_repository import TransactionRepository
            from app.core.repositories.category_repository import CategoryRepository
            
            transaction_repo = TransactionRepository(supabase)
            category_repo = CategoryRepository(supabase)
            
            recent_transactions = await transaction_repo.get_transactions(0, 20)
            
            output = "Recent Transactions:\n\n"
            for t in recent_transactions:
                # Get category name if available
                category_name = "Uncategorized"
                if t.category_id:
                    category = await category_repo.get_category(str(t.category_id))
                    if category:
                        category_name = category.name
                
                # Format date for better readability
                date_str = t.date.strftime("%Y-%m-%d %H:%M") if hasattr(t.date, 'strftime') else str(t.date)
                
                output += f"• {date_str} - ₹{float(t.amount):.2f} at {t.merchant} ({category_name})\n"
            
            return output
        except Exception as e:
            return f"Error loading transactions: {str(e)}"
    
    
    @mcp.resource("expense-tracker://available-tags")
    async def available_tags_resource() -> str:
        """Resource providing all available predefined tags for expense categorization"""
        try:
            # Organize tags by category
            tag_categories = {
                "Subscription Frequency": {
                    "annual-subscription": "Yearly subscription payment",
                    "monthly-subscription": "Monthly subscription payment",
                    "quarterly-subscription": "Quarterly subscription payment"
                },
                "Expense Type": {
                    "recurring": "Regular recurring expense",
                    "one-time": "One-time purchase",
                    "subscription": "General subscription service"
                },
                "Category": {
                    "business": "Business related expense",
                    "personal": "Personal expense",
                    "travel": "Travel related expense",
                    "online": "Online purchase"
                },
                "Special": {
                    "tax-deductible": "Tax deductible expense",
                    "reimbursable": "Expense eligible for reimbursement",
                    "shared": "Shared expense with others"
                },
                "Payment Method": {
                    "cash": "Cash payment",
                    "credit-card": "Credit card payment",
                    "debit-card": "Debit card payment",
                    "bank-transfer": "Bank transfer payment"
                }
            }
            
            output = "Available Tags for Expense Tracking:\n\n"
            output += "IMPORTANT: Only use these predefined tags when creating or updating transactions.\n\n"
            
            for category, tags in tag_categories.items():
                output += f"📌 {category}:\n"
                for tag, description in tags.items():
                    output += f"   • {tag} - {description}\n"
                output += "\n"
            
            output += "💡 Tips:\n"
            output += "   - Multiple tags can be applied to a single transaction\n"
            output += "   - Use subscription frequency tags for recurring payments\n"
            output += "   - Add payment method tags for better tracking\n"
            output += "   - Apply special tags for tax or reimbursement purposes"
            
            return output
        except Exception as e:
            return f"Error loading available tags: {str(e)}"