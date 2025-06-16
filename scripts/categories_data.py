"""
Default expense categories for upload to Supabase
"""

# Comprehensive expense categories with hierarchical structure
DEFAULT_CATEGORIES = [
    # Food & Dining
    {
        "name": "Food & Dining",
        "subcategories": [
            "Groceries",
            "Restaurants", 
            "Fast Food",
            "Coffee & Tea",
            "Bars & Alcohol",
            "Food Delivery"
        ]
    },
    
    # Transportation
    {
        "name": "Transportation",
        "subcategories": [
            "Gas & Fuel",
            "Public Transit",
            "Rideshare & Taxi",
            "Car Maintenance",
            "Car Insurance",
            "Parking",
            "Tolls"
        ]
    },
    
    # Shopping & Supplies
    {
        "name": "Shopping & Supplies",
        "subcategories": [
            "Clothing",
            "Electronics",
            "Home & Garden",
            "Personal Care",
            "Household Supplies",
            "Books & Media",
            "Gifts"
        ]
    },
    
    # Housing & Utilities
    {
        "name": "Housing & Utilities",
        "subcategories": [
            "Rent",
            "Mortgage",
            "Electricity",
            "Gas",
            "Water",
            "Internet",
            "Phone",
            "Cable/Streaming",
            "Home Insurance",
            "Property Tax"
        ]
    },
    
    # Healthcare & Medical
    {
        "name": "Healthcare & Medical",
        "subcategories": [
            "Doctor Visits",
            "Prescriptions",
            "Dental",
            "Vision",
            "Health Insurance",
            "Medical Supplies"
        ]
    },
    
    # Entertainment & Recreation
    {
        "name": "Entertainment & Recreation",
        "subcategories": [
            "Movies & Theater",
            "Sports & Fitness",
            "Hobbies",
            "Travel & Vacation",
            "Gaming",
            "Music & Concerts"
        ]
    },
    
    # Financial & Banking
    {
        "name": "Financial & Banking",
        "subcategories": [
            "Bank Fees",
            "ATM Fees",
            "Investment Fees",
            "Credit Card Fees",
            "Loan Payments",
            "Insurance Premiums"
        ]
    },
    
    # Education & Learning
    {
        "name": "Education & Learning",
        "subcategories": [
            "Tuition",
            "Books & Supplies",
            "Online Courses",
            "Workshops",
            "Certification"
        ]
    },
    
    # Work & Business
    {
        "name": "Work & Business",
        "subcategories": [
            "Office Supplies",
            "Business Travel",
            "Professional Services",
            "Software & Tools",
            "Equipment"
        ]
    },
    
    # Personal & Family
    {
        "name": "Personal & Family",
        "subcategories": [
            "Childcare",
            "Pet Care",
            "Personal Services",
            "Subscriptions",
            "Donations",
            "Legal Services"
        ]
    },
    
    # Miscellaneous
    {
        "name": "Miscellaneous",
        "subcategories": [
            "Other",
            "Uncategorized",
            "Cash Withdrawal",
            "Transfers"
        ]
    }
]

# Flat list for simple upload (without hierarchy)
FLAT_CATEGORIES = [
    # Food & Dining
    "Food & Dining",
    "Groceries", 
    "Restaurants",
    "Fast Food",
    "Coffee & Tea",
    "Bars & Alcohol",
    "Food Delivery",
    
    # Transportation
    "Transportation",
    "Gas & Fuel",
    "Public Transit",
    "Rideshare & Taxi", 
    "Car Maintenance",
    "Car Insurance",
    "Parking",
    "Tolls",
    
    # Shopping & Supplies
    "Shopping & Supplies",
    "Clothing",
    "Electronics",
    "Home & Garden",
    "Personal Care",
    "Household Supplies",
    "Books & Media",
    "Gifts",
    
    # Housing & Utilities
    "Housing & Utilities",
    "Rent",
    "Mortgage",
    "Electricity",
    "Gas",
    "Water",
    "Internet",
    "Phone",
    "Cable/Streaming",
    "Home Insurance",
    "Property Tax",
    
    # Healthcare & Medical
    "Healthcare & Medical",
    "Doctor Visits",
    "Prescriptions",
    "Dental",
    "Vision",
    "Health Insurance",
    "Medical Supplies",
    
    # Entertainment & Recreation
    "Entertainment & Recreation",
    "Movies & Theater",
    "Sports & Fitness",
    "Hobbies",
    "Travel & Vacation",
    "Gaming",
    "Music & Concerts",
    
    # Financial & Banking
    "Financial & Banking",
    "Bank Fees",
    "ATM Fees",
    "Investment Fees",
    "Credit Card Fees",
    "Loan Payments",
    "Insurance Premiums",
    
    # Education & Learning
    "Education & Learning",
    "Tuition",
    "Books & Supplies",
    "Online Courses",
    "Workshops",
    "Certification",
    
    # Work & Business
    "Work & Business",
    "Office Supplies",
    "Business Travel",
    "Professional Services",
    "Software & Tools",
    "Equipment",
    
    # Personal & Family
    "Personal & Family",
    "Childcare",
    "Pet Care",
    "Personal Services",
    "Subscriptions",
    "Donations",
    "Legal Services",
    
    # Miscellaneous
    "Miscellaneous",
    "Other",
    "Uncategorized",
    "Cash Withdrawal",
    "Transfers"
]