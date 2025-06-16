"""
MCP Prompts for Expense Tracker - System prompts and instructions
"""
from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP):
    """Register all MCP prompts with the server"""
    
    @mcp.prompt(name="add_transaction", description="Instructions for parsing natural language transaction descriptions")
    def add_transaction_prompt() -> str:
        """Instructions for adding a new transaction"""
        return """Transaction Entry Instructions:

Parse natural language transaction descriptions and extract:

1. Required Information:
   - Amount: The transaction amount in rupees
     * User provides amount as spent (e.g., "12" means spent ₹12)
     * Convert to negative for expenses/debits (money spent)
     * Keep positive for income/credits (money received)
   - Date: When the transaction occurred
     * Parse dates like "12 june", "yesterday", "today", "last monday"
     * Include time if provided (e.g., "6pm")
     * Default to current date if not specified
   - Merchant: Where the transaction occurred
     * Extract business/merchant name from description
   - Category: Use get_categories() to find the appropriate category
     * Match based on merchant type and transaction context

2. Optional Information:
   - Tags: Apply relevant tags if mentioned or implied
     * Use get_available_tags() to see valid tags
     * Common tags: "cash", "personal", "business", "recurring"
   - Notes: Any additional context or details
     * Item details, purpose, or other relevant information

3. Example Parsing:
   Input: "i bought maggi on 12 june, 6pm for rs 12"
   
   Extracted:
   - Amount: -12 (negative because it's an expense)
   - Date: June 12, 6:00 PM (current year)
   - Merchant: Store name (if not specified, use generic like "Grocery Store")
   - Category: "Food & Dining" or "Groceries"
   - Tags: ["personal", "cash"] (if payment method implied)
   - Notes: "Maggi noodles"

4. Category Selection:
   - First check available categories using get_categories()
   - Match based on merchant type:
     * Grocery items → "Groceries" or "Food & Dining"
     * Restaurant/cafe → "Food & Dining"
     * Fuel/petrol → "Transportation"
     * Online shopping → "Shopping"
   - When uncertain, use the most specific applicable category

5. Amount Handling:
   - Expenses (money spent): Make negative
   - Income (money received): Keep positive
   - The user may provide negative amounts directly (e.g., "-100" means already an expense)
   - Examples:
     * "spent 100" → -100
     * "received 500" → +500
     * "paid 50" → -50
     * "earned 1000" → +1000
     * "bought for -180" → -180 (already negative, keep as is)
   
CRITICAL: When using the create_expense tool, always pass:
- NEGATIVE amounts for expenses/debits
- POSITIVE amounts for income/credits

Always extract as much information as possible from the natural language description.
"""