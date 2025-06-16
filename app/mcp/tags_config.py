"""
Predefined tags configuration for expense tracking
"""

# Define allowed tags with descriptions
PREDEFINED_TAGS = {
    # Subscription frequency tags
    "annual-subscription": "Yearly subscription payment",
    "monthly-subscription": "Monthly subscription payment", 
    "quarterly-subscription": "Quarterly subscription payment",
    
    # Expense type tags
    "recurring": "Regular recurring expense",
    "one-time": "One-time purchase",
    "subscription": "General subscription service",
    
    # Category tags
    "business": "Business related expense",
    "personal": "Personal expense",
    "travel": "Travel related expense",
    "online": "Online purchase",
    
    # Special tags
    "tax-deductible": "Tax deductible expense",
    "reimbursable": "Expense eligible for reimbursement",
    "shared": "Shared expense with others",
    
    # Payment method tags
    "cash": "Cash payment",
    "credit-card": "Credit card payment",
    "debit-card": "Debit card payment",
    "bank-transfer": "Bank transfer payment"
}

# Get list of valid tag values
VALID_TAGS = list(PREDEFINED_TAGS.keys())

def validate_tags(tags: list) -> tuple[bool, list]:
    """
    Validate if all provided tags are in the predefined list
    Returns: (is_valid, invalid_tags)
    """
    if not tags:
        return True, []
    
    invalid_tags = [tag for tag in tags if tag not in VALID_TAGS]
    return len(invalid_tags) == 0, invalid_tags

def get_tag_description(tag: str) -> str:
    """Get description for a specific tag"""
    return PREDEFINED_TAGS.get(tag, "Unknown tag")