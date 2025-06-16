"""
MCP Prompts for Expense Tracker - System prompts and instructions
"""
from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP):
    """Register all MCP prompts with the server"""
    
    @mcp.prompt(name="receipt_parser")
    def receipt_parser_prompt() -> str:
        """Instructions for parsing receipts and bank statements"""
        return """Receipt and Bank Statement Parsing Instructions:

When parsing financial documents:

1. Extract Key Information:
   - Transaction date (use exact date from document)
   - Amount (include decimals, convert to positive number)
   - Merchant name (use full business name)
   - Payment method (if available)

2. Categorization Rules:
   - Match merchant names to appropriate categories
   - Look for keywords in merchant names
   - Consider transaction amounts for context
   - Check for recurring patterns

3. Common Merchant Patterns:
   - "AMZN" or "AMAZON" → Shopping (Online Shopping)
   - "UBER" or "LYFT" → Transportation (Ride Sharing)
   - "STARBUCKS" or "COFFEE" → Food & Dining (Coffee & Tea)
   - "NETFLIX" or "SPOTIFY" → Entertainment (Subscriptions)
   - Gas station names → Transportation (Fuel)
   - Restaurant names → Food & Dining (Restaurants)

4. Tags to Apply (use ONLY these predefined tags):
   
   Subscription Frequency:
   - "annual-subscription" for yearly payments
   - "monthly-subscription" for monthly payments
   - "quarterly-subscription" for quarterly payments
   
   Expense Type:
   - "subscription" for recurring services
   - "recurring" for regular expenses
   - "one-time" for single purchases
   
   Category Tags:
   - "online" for e-commerce
   - "business" for work-related expenses
   - "personal" for personal expenses
   - "travel" for trip-related costs
   
   Special Tags:
   - "tax-deductible" for deductible expenses
   - "reimbursable" for reimbursable expenses
   - "shared" for shared expenses
   
   Payment Method:
   - "cash", "credit-card", "debit-card", "bank-transfer"
   
   IMPORTANT: Only use tags from the above list. Call get_available_tags() to see all valid tags.

5. Notes Guidelines:
   - Add item details for shopping receipts
   - Include purpose for business expenses
   - Note if expense is tax-deductible
   - Mention if part of a larger purchase
   - For subscriptions: Include period covered (e.g., "Annual plan: Jan 2024 - Dec 2024")
   - For annual payments: Calculate monthly equivalent (e.g., "₹100/year = ₹8.33/month")

Always maintain accuracy and don't make assumptions about missing information.
"""