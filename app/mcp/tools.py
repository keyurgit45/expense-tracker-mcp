"""
MCP Tools for Expense Tracker - All tool implementations
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
import logging

from mcp.server.fastmcp import FastMCP

from app.database import supabase
from app.crud import categories, transactions
from app.crud import tags as tags_crud
from app.schemas.schemas import CategoryCreate, TransactionCreate, TransactionUpdate, TagCreate, TransactionTagCreate
from app.mcp.tags_config import validate_tags, VALID_TAGS, PREDEFINED_TAGS

# Configure logging for MCP
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_tools(mcp: FastMCP):
    """Register all MCP tools with the server"""
    
    @mcp.tool()
    async def create_expense(
        date: str, 
        amount: float, 
        merchant: str, 
        category: str = None, 
        notes: str = None, 
        tags: List[str] = None,
        auto_categorize: bool = True
    ) -> dict:
        """
        Create a new expense transaction from bank statement or receipt data.
        This is the primary tool for adding expenses to the tracking system.
        
        IMPORTANT: Amount should be:
        - NEGATIVE for expenses/debits (money spent)
        - POSITIVE for income/credits (money received)
        
        Examples:
        - Bought groceries for 100: amount = -100
        - Received salary 50000: amount = 50000
        - Paid rent 15000: amount = -15000
        
        If auto_categorize is True and no category is provided, will attempt to 
        automatically categorize the transaction using AI/embeddings.
        """
        try:
            logger.info(f"Creating expense: date={date}, amount={amount}, merchant={merchant}, category={category}, auto_categorize={auto_categorize}")
            logger.debug(f"Tags provided: {tags}")
            logger.debug(f"Notes: {notes}")
            
            # Set defaults
            if tags is None:
                tags = []
            
            # Validate tags
            is_valid, invalid_tags = validate_tags(tags)
            if not is_valid:
                logger.error(f"Invalid tags detected: {invalid_tags}")
                return {
                    "success": False,
                    "error": f"Invalid tags: {', '.join(invalid_tags)}. Valid tags are: {', '.join(VALID_TAGS)}"
                }
                
            # Convert date string to datetime object with timezone
            # Handle both date-only and datetime inputs
            logger.debug(f"Parsing date: {date}")
            if len(date) == 10:  # YYYY-MM-DD format
                transaction_date = datetime.strptime(date, "%Y-%m-%d")
                logger.debug(f"Parsed as date-only: {transaction_date}")
            else:  # Full datetime format
                try:
                    transaction_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    logger.debug(f"Parsed as ISO format: {transaction_date}")
                except:
                    transaction_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                    logger.debug(f"Parsed as datetime format: {transaction_date}")
            
            # Ensure timezone awareness (default to UTC if naive)
            if transaction_date.tzinfo is None:
                transaction_date = transaction_date.replace(tzinfo=timezone.utc)
                logger.debug(f"Added UTC timezone: {transaction_date}")
            
            # Find or create category
            category_id = None
            auto_categorized = False
            auto_category_confidence = None
            manual_category_id = None
            manual_category_name = category  # Store the provided category name
            
            # First, get the manual category ID if provided (we'll use it as fallback)
            if category:
                logger.info(f"Manual category provided as fallback: {category}")
                existing_category = await categories.get_category_by_name(supabase, category)
                if not existing_category:
                    # Create new category if it doesn't exist
                    logger.info(f"Creating new category: {category}")
                    new_category = await categories.create_category(
                        supabase, 
                        CategoryCreate(name=category)
                    )
                    manual_category_id = new_category.category_id
                    logger.debug(f"New category created with ID: {manual_category_id}")
                else:
                    manual_category_id = existing_category.category_id
                    logger.debug(f"Found existing category with ID: {manual_category_id}")
            
            # Always try auto-categorization first (regardless of auto_categorize flag)
            if auto_categorize:
                logger.info("Attempting auto-categorization")
                # First try embeddings
                try:
                    from app.services.categorization_free import FreeCategorizationService
                    
                    logger.debug("Initializing FreeCategorizationService")
                    service = FreeCategorizationService()
                    # Create a temporary transaction object for categorization
                    temp_transaction = type('obj', (object,), {
                        'merchant': merchant,
                        'amount': Decimal(str(amount)),
                        'notes': notes,
                        'date': transaction_date  # Add the date attribute
                    })
                    
                    logger.debug(f"Calling categorize_transaction with merchant={merchant}, notes={notes}")
                    predicted_category_id, predicted_category_name, confidence = await service.categorize_transaction(
                        temp_transaction,
                        description=notes
                    )
                    
                    logger.info(f"Embedding categorization result: category={predicted_category_name}, confidence={confidence}")
                    
                    if predicted_category_id and confidence >= 0.7:
                        category_id = predicted_category_id
                        category = predicted_category_name
                        auto_categorized = True
                        auto_category_confidence = round(confidence * 100, 1)
                        logger.info(f"Using embedding categorization: {category} with {auto_category_confidence}% confidence")
                except Exception as e:
                    # Embeddings failed, try rule-based
                    logger.warning(f"Embedding categorization failed: {str(e)}")
                    logger.debug("Falling back to rule-based categorization")
                
                # Fallback to rule-based if embeddings didn't work
                if not category_id:
                    merchant_lower = merchant.lower() if merchant else ""
                    notes_lower = notes.lower() if notes else ""
                    combined_text = f"{merchant_lower} {notes_lower}"
                    logger.debug(f"Applying rule-based categorization on: {combined_text}")
                    
                    # Enhanced rules with more patterns
                    if any(food in combined_text for food in ["restaurant", "cafe", "coffee", "pizza", "burger", "food", "dining", "eat"]):
                        category = "Food & Dining"
                    elif any(transport in combined_text for transport in ["uber", "ola", "taxi", "fuel", "petrol", "gas", "parking", "toll"]):
                        category = "Transportation"
                    elif any(shopping in combined_text for shopping in ["amazon", "flipkart", "store", "mart", "shop", "mall"]):
                        category = "Shopping"
                    elif any(health in combined_text for health in ["medicine", "medical", "doctor", "hospital", "pharmacy", "health", "clinic", "lab", "labs", "test", "covid", "diagnostic", "scan", "xray", "x-ray"]):
                        category = "Healthcare"
                    elif any(utility in combined_text for utility in ["electricity", "water", "gas", "internet", "phone", "mobile"]):
                        category = "Utilities"
                    elif any(housing in combined_text for housing in ["rent", "mortgage", "maintenance", "repair"]):
                        category = "Housing"
                    
                    if category:
                        logger.info(f"Rule-based categorization matched: {category}")
                        existing_category = await categories.get_category_by_name(supabase, category)
                        if existing_category:
                            category_id = existing_category.category_id
                            auto_categorized = True
                            auto_category_confidence = 0  # Rule-based
                            logger.debug(f"Found category ID: {category_id}")
                    else:
                        logger.info("No rule-based category match found")
            
            # If auto-categorization didn't find a category, use the manual category as fallback
            if not category_id and manual_category_id:
                logger.info(f"Auto-categorization failed, using manual category: {manual_category_name}")
                category_id = manual_category_id
                category = manual_category_name
                # Note: We don't set auto_categorized=True here since it was manually provided
            
            # Create transaction
            logger.info(f"Creating transaction with category_id={category_id}")
            transaction_data = TransactionCreate(
                date=transaction_date,
                amount=Decimal(str(amount)),
                merchant=merchant,
                category_id=category_id,
                notes=notes
            )
            
            logger.debug(f"Transaction data: date={transaction_date}, amount={amount}, merchant={merchant}")
            new_transaction = await transactions.create_transaction(supabase, transaction_data)
            logger.info(f"Transaction created successfully with ID: {new_transaction.transaction_id}")
            
            # Store embedding for future learning if transaction has a category
            if category_id and category:
                try:
                    # Determine confidence score for embedding storage
                    embedding_confidence = 1.0  # Default for manual/fallback categories
                    if auto_categorized and auto_category_confidence is not None:
                        embedding_confidence = auto_category_confidence / 100.0
                    
                    logger.debug(f"Storing embedding for learning: category={category}, confidence={embedding_confidence}")
                    from app.services.categorization_free import FreeCategorizationService
                    service = FreeCategorizationService()
                    
                    # Store the embedding with the transaction details
                    await service.store_transaction_embedding(
                        transaction_id=new_transaction.transaction_id,
                        transaction_text=service.embedding_service.format_transaction_text(
                            date=transaction_date,
                            amount=new_transaction.amount,
                            merchant=merchant,
                            description=notes,
                            category=category
                        ),
                        category_id=category_id,
                        category_name=category,
                        confidence_score=embedding_confidence
                    )
                    logger.info(f"Embedding stored successfully for transaction {new_transaction.transaction_id}")
                except Exception as e:
                    logger.warning(f"Failed to store embedding for learning: {str(e)}")
                    import traceback
                    logger.debug(f"Embedding storage error traceback: {traceback.format_exc()}")
                    pass  # Don't fail the transaction if embedding storage fails
            
            # Add tags if provided
            created_tags = []
            if tags:  # Only process if tags is not empty
                logger.debug(f"Processing {len(tags)} tags")
                for tag_value in tags:
                    logger.debug(f"Processing tag: {tag_value}")
                    # Try to find existing tag
                    existing_tag = await tags_crud.get_tag_by_value(supabase, tag_value)
                    if not existing_tag:
                        # Create new tag
                        logger.debug(f"Creating new tag: {tag_value}")
                        new_tag = await tags_crud.create_tag(supabase, TagCreate(value=tag_value))
                        existing_tag = new_tag
                    
                    # Link tag to transaction
                    await tags_crud.add_tag_to_transaction(
                        supabase, 
                        TransactionTagCreate(
                            transaction_id=new_transaction.transaction_id,
                            tag_id=existing_tag.tag_id
                        )
                    )
                    created_tags.append(tag_value)
                logger.info(f"Added {len(created_tags)} tags to transaction")
            
            result = {
                "success": True,
                "transaction_id": str(new_transaction.transaction_id),
                "message": f"Created expense: ${amount} at {merchant}",
                "category": category,
                "tags": created_tags
            }
            
            if auto_categorized:
                result["auto_categorized"] = True
                if auto_category_confidence is not None:
                    result["category_confidence"] = auto_category_confidence
            
            logger.info(f"Successfully created transaction: {result['transaction_id']}")
            return result
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to create expense: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": error_msg,
                "traceback": traceback.format_exc()
            }

    @mcp.tool()
    async def update_transaction(
        transaction_id: str,
        date: Optional[str] = None,
        amount: Optional[float] = None,
        merchant: Optional[str] = None,
        category: Optional[str] = None,
        notes: Optional[str] = None,
        is_recurring: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> dict:
        """
        Update an existing expense transaction.
        All fields are optional - only provide the fields you want to update.
        """
        try:
            logger.info(f"Updating transaction {transaction_id}")
            logger.debug(f"Update params: date={date}, amount={amount}, merchant={merchant}, category={category}, tags={tags}")
            
            # Check if transaction exists
            existing_transaction = await transactions.get_transaction(supabase, transaction_id)
            if not existing_transaction:
                logger.error(f"Transaction {transaction_id} not found")
                return {
                    "success": False,
                    "error": f"Transaction with ID {transaction_id} not found"
                }
            
            # Validate tags if provided
            if tags is not None:
                is_valid, invalid_tags = validate_tags(tags)
                if not is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid tags: {', '.join(invalid_tags)}. Valid tags are: {', '.join(VALID_TAGS)}"
                    }
            
            # Build update data
            update_data = {}
            
            # Handle date update
            if date is not None:
                if len(date) == 10:  # YYYY-MM-DD format
                    transaction_date = datetime.strptime(date, "%Y-%m-%d")
                else:  # Full datetime format
                    try:
                        transaction_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    except:
                        transaction_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                
                # Ensure timezone awareness (default to UTC if naive)
                if transaction_date.tzinfo is None:
                    transaction_date = transaction_date.replace(tzinfo=timezone.utc)
                
                update_data['date'] = transaction_date
            
            # Handle amount update
            if amount is not None:
                update_data['amount'] = Decimal(str(amount))
            
            # Handle merchant update
            if merchant is not None:
                update_data['merchant'] = merchant
            
            # Handle category update
            if category is not None:
                # Try to find existing category by name
                existing_category = await categories.get_category_by_name(supabase, category)
                if not existing_category:
                    # Create new category if it doesn't exist
                    new_category = await categories.create_category(
                        supabase, 
                        CategoryCreate(name=category)
                    )
                    update_data['category_id'] = new_category.category_id
                else:
                    update_data['category_id'] = existing_category.category_id
            
            # Handle is_recurring update
            if is_recurring is not None:
                update_data['is_recurring'] = is_recurring
            
            # Handle notes update
            if notes is not None:
                update_data['notes'] = notes
            
            # Update transaction if there are changes
            if update_data:
                transaction_update = TransactionUpdate(**update_data)
                updated_transaction = await transactions.update_transaction(
                    supabase, 
                    transaction_id, 
                    transaction_update
                )
                
                if not updated_transaction:
                    return {
                        "success": False,
                        "error": "Failed to update transaction"
                    }
            else:
                updated_transaction = existing_transaction
            
            # Handle tags update if provided
            updated_tags = []
            if tags is not None:
                # First, remove all existing tags
                await supabase.table("transaction_tags").delete().eq("transaction_id", transaction_id).execute()
                
                # Add new tags
                for tag_value in tags:
                    # Try to find existing tag
                    existing_tag = await tags_crud.get_tag_by_value(supabase, tag_value)
                    if not existing_tag:
                        # Create new tag
                        new_tag = await tags_crud.create_tag(supabase, TagCreate(value=tag_value))
                        existing_tag = new_tag
                    
                    # Link tag to transaction
                    await tags_crud.add_tag_to_transaction(
                        supabase, 
                        TransactionTagCreate(
                            transaction_id=transaction_id,
                            tag_id=existing_tag.tag_id
                        )
                    )
                    updated_tags.append(tag_value)
            
            # Get updated transaction details
            transaction_details = await transactions.get_transaction_with_tags(supabase, transaction_id)
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "message": f"Updated transaction: ${updated_transaction.amount} at {updated_transaction.merchant}",
                "updated_fields": list(update_data.keys()) + (["tags"] if tags is not None else []),
                "tags": updated_tags if tags is not None else [tag.value for tag in transaction_details.tags]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update transaction: {str(e)}"
            }

    @mcp.tool()
    async def get_spending_summary(days: int = 30) -> dict:
        """
        Get spending summary and insights for analysis.
        Returns total spending, transaction count, and top categories by spending.
        """
        try:
            logger.info(f"Getting spending summary for {days} days")
            # Get all transactions (in a real app, you'd filter by date range)
            all_transactions = await transactions.get_transactions(supabase, 0, 1000)
            logger.debug(f"Retrieved {len(all_transactions) if all_transactions else 0} transactions")
            
            if not all_transactions:
                return {
                    "total_amount": 0.0,
                    "transaction_count": 0,
                    "top_categories": [],
                    "message": "No transactions found"
                }
            
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
            
            return {
                "total_amount": round(total_amount, 2),
                "transaction_count": transaction_count,
                "top_categories": top_categories,
                "average_transaction": round(total_amount / transaction_count, 2) if transaction_count > 0 else 0,
                "message": f"Analyzed {transaction_count} transactions totaling ${total_amount:.2f}"
            }
            
        except Exception as e:
            logger.error(f"Failed to get spending summary: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get spending summary: {str(e)}"
            }


    @mcp.tool()
    async def get_available_categories() -> dict:
        """
        Get all available expense categories for proper categorization.
        Returns hierarchical structure with parent and child categories.
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
            return {
                "success": False,
                "error": f"Failed to get categories: {str(e)}"
            }

    @mcp.tool()
    async def get_recent_transactions(limit: int = 10) -> dict:
        """
        Get recent transactions for context and analysis.
        Useful for understanding spending patterns and finding similar transactions.
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
                
                # Format date for better readability
                date_str = t.date.strftime("%Y-%m-%d %H:%M") if hasattr(t.date, 'strftime') else str(t.date)
                
                formatted_transactions.append({
                    "date": date_str,
                    "amount": float(t.amount),
                    "merchant": t.merchant,
                    "category": category_name,
                    "notes": t.notes,
                    "id": str(t.transaction_id)
                })
            
            return {
                "transactions": formatted_transactions,
                "count": len(formatted_transactions),
                "message": f"Retrieved {len(formatted_transactions)} recent transactions"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get recent transactions: {str(e)}"
            }

    @mcp.tool()
    async def analyze_subscriptions() -> dict:
        """
        Analyze recurring and subscription expenses.
        Identifies monthly, annual, and other periodic payments.
        """
        try:
            logger.info("Analyzing subscription expenses")
            # Get all transactions with subscription-related tags
            all_transactions = await transactions.get_transactions(supabase, 0, 1000)
            logger.debug(f"Found {len(all_transactions) if all_transactions else 0} total transactions")
            
            subscription_transactions = []
            for t in all_transactions:
                # Get transaction with tags
                t_with_tags = await transactions.get_transaction_with_tags(supabase, str(t.transaction_id))
                if t_with_tags and t_with_tags.tags:
                    tag_values = [tag.value for tag in t_with_tags.tags]
                    if any(tag in tag_values for tag in ['subscription', 'annual-subscription', 'monthly-subscription', 'quarterly-subscription', 'recurring']):
                        subscription_transactions.append(t_with_tags)
                        logger.debug(f"Found subscription transaction: {t_with_tags.merchant} with tags {tag_values}")
            
            logger.info(f"Found {len(subscription_transactions)} subscription transactions")
            
            # Analyze subscriptions
            monthly_subs = []
            annual_subs = []
            other_subs = []
            
            for sub in subscription_transactions:
                tag_values = [tag.value for tag in sub.tags]
                sub_info = {
                    "merchant": sub.merchant,
                    "amount": float(sub.amount),
                    "date": sub.date.strftime("%Y-%m-%d") if hasattr(sub.date, 'strftime') else str(sub.date),
                    "notes": sub.notes,
                    "tags": tag_values
                }
                
                if 'annual-subscription' in tag_values:
                    sub_info["monthly_equivalent"] = round(float(sub.amount) / 12, 2)
                    annual_subs.append(sub_info)
                elif 'monthly-subscription' in tag_values:
                    sub_info["annual_cost"] = round(float(sub.amount) * 12, 2)
                    monthly_subs.append(sub_info)
                elif 'quarterly-subscription' in tag_values:
                    sub_info["monthly_equivalent"] = round(float(sub.amount) / 3, 2)
                    sub_info["annual_cost"] = round(float(sub.amount) * 4, 2)
                    other_subs.append(sub_info)
                else:
                    other_subs.append(sub_info)
            
            # Calculate totals
            total_monthly = sum(s["amount"] for s in monthly_subs)
            total_annual_equivalent = (
                total_monthly * 12 + 
                sum(s["amount"] for s in annual_subs) +
                sum(s.get("annual_cost", 0) for s in other_subs if "annual_cost" in s)
            )
            
            return {
                "monthly_subscriptions": monthly_subs,
                "annual_subscriptions": annual_subs,
                "other_subscriptions": other_subs,
                "monthly_total": round(total_monthly, 2),
                "annual_total_equivalent": round(total_annual_equivalent, 2),
                "message": f"Found {len(subscription_transactions)} subscription expenses"
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze subscriptions: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to analyze subscriptions: {str(e)}"
            }
    
    @mcp.tool()
    async def confirm_transaction_category(
        transaction_id: str,
        category_name: str,
        store_embedding: bool = True
    ) -> dict:
        """
        Confirm or correct a transaction's category.
        This feeds back into the learning system to improve future predictions.
        """
        try:
            # Get transaction
            transaction = await transactions.get_transaction(supabase, transaction_id)
            if not transaction:
                return {
                    "success": False,
                    "error": f"Transaction with ID {transaction_id} not found"
                }
            
            # Find category by name
            existing_category = await categories.get_category_by_name(supabase, category_name)
            if not existing_category:
                return {
                    "success": False,
                    "error": f"Category '{category_name}' not found"
                }
            
            # Update transaction category
            update_data = TransactionUpdate(category_id=existing_category.category_id)
            updated = await transactions.update_transaction(
                supabase,
                transaction_id,
                update_data
            )
            
            if not updated:
                return {
                    "success": False,
                    "error": "Failed to update transaction"
                }
            
            # Store embedding for learning if requested
            if store_embedding:
                try:
                    from app.services.categorization_free import FreeCategorizationService
                    
                    service = FreeCategorizationService()
                    await service.learn_from_feedback(
                        transaction,
                        existing_category.category_id,
                        existing_category.name,
                        description=transaction.notes
                    )
                    
                    return {
                        "success": True,
                        "category_confirmed": existing_category.name,
                        "embedding_stored": True,
                        "message": f"Category confirmed as '{existing_category.name}' and stored for future learning"
                    }
                except Exception as e:
                    # Category updated but embedding failed
                    return {
                        "success": True,
                        "category_confirmed": existing_category.name,
                        "embedding_stored": False,
                        "message": f"Category confirmed but embedding storage failed: {str(e)}"
                    }
            
            return {
                "success": True,
                "category_confirmed": existing_category.name,
                "embedding_stored": False,
                "message": f"Category confirmed as '{existing_category.name}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to confirm category: {str(e)}"
            }

