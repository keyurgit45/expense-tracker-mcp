"""
Free intelligent transaction categorization service using local embeddings and rule-based logic
"""
import json
from typing import List, Optional, Tuple, Dict
from decimal import Decimal
from datetime import datetime
import uuid

from app.database import supabase
from app.services.embeddings_free import FreeEmbeddingService
from app.crud import categories as categories_crud
from app.schemas.schemas import TransactionResponse


class FreeCategorizationService:
    """Service for intelligent transaction categorization without external APIs"""
    
    def __init__(self):
        self.embedding_service = FreeEmbeddingService()
        self.similarity_threshold = 0.7
        self.top_k = 5
        
    async def find_similar_transactions(
        self,
        transaction_text: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar transactions using vector similarity search
        
        Returns list of similar transactions with their categories
        """
        # Generate embedding for the query text
        query_embedding = await self.embedding_service.generate_embedding(transaction_text)
        
        # Convert to PostgreSQL array format
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Call the stored function to find similar transactions
        try:
            result = supabase.rpc(
                "find_similar_transactions",
                {
                    "query_embedding": embedding_str,
                    "limit_count": limit,
                    "similarity_threshold": self.similarity_threshold
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to find similar transactions: {str(e)}")
            return []
    
    async def categorize_transaction(
        self,
        transaction: TransactionResponse,
        description: Optional[str] = None
    ) -> Tuple[Optional[uuid.UUID], Optional[str], float]:
        """
        Categorize a transaction using similarity search and rule-based logic
        
        Returns:
            Tuple of (category_id, category_name, confidence_score)
        """
        # Format transaction text without category
        transaction_text = self.embedding_service.format_transaction_text(
            date=transaction.date,
            amount=transaction.amount,
            merchant=transaction.merchant,
            description=description
        )
        
        # Find similar transactions
        similar_transactions = await self.find_similar_transactions(
            transaction_text,
            limit=self.top_k
        )
        
        if not similar_transactions:
            # No similar transactions found, use rule-based approach
            return await self._rule_based_categorization(transaction)
        
        # Check if we have high confidence based on similarity
        if similar_transactions[0]["similarity_score"] >= 0.85:
            # Very similar transaction found, use its category
            return (
                similar_transactions[0]["confirmed_category_id"],
                similar_transactions[0]["confirmed_category_name"],
                similar_transactions[0]["similarity_score"]
            )
        
        # Use weighted voting from similar transactions
        category_votes = {}
        total_weight = 0
        
        for tx in similar_transactions:
            weight = tx["similarity_score"]
            category_name = tx["confirmed_category_name"]
            
            if category_name in category_votes:
                category_votes[category_name]["weight"] += weight
                category_votes[category_name]["count"] += 1
            else:
                category_votes[category_name] = {
                    "weight": weight,
                    "count": 1,
                    "category_id": tx["confirmed_category_id"]
                }
            
            total_weight += weight
        
        # Find the most voted category
        if category_votes:
            best_category = max(category_votes.items(), key=lambda x: x[1]["weight"])
            category_name = best_category[0]
            category_info = best_category[1]
            confidence = category_info["weight"] / total_weight
            
            # If confidence is still low, use rule-based as fallback
            if confidence < 0.5:
                return await self._rule_based_categorization(transaction)
            
            return (
                category_info["category_id"],
                category_name,
                confidence
            )
        
        # Fallback to rule-based
        return await self._rule_based_categorization(transaction)
    
    async def _rule_based_categorization(
        self,
        transaction: TransactionResponse
    ) -> Tuple[Optional[uuid.UUID], Optional[str], float]:
        """
        Rule-based categorization as fallback
        """
        merchant_lower = transaction.merchant.lower() if transaction.merchant else ""
        amount = float(transaction.amount)
        
        # Define rules with confidence scores
        rules = [
            # Food & Dining rules
            (["restaurant", "cafe", "coffee", "starbucks", "pizza", "burger", "food"], 
             "Food & Dining", 0.8),
            (["swiggy", "zomato", "uber eats"], 
             "Food & Dining", 0.9),
            
            # Transportation rules
            (["uber", "ola", "taxi", "cab", "lyft"], 
             "Transportation", 0.9),
            (["petrol", "fuel", "gas station", "indian oil", "bharat petroleum"], 
             "Transportation", 0.85),
            
            # Shopping rules
            (["amazon", "flipkart", "myntra", "ajio", "store", "mart", "mall"], 
             "Shopping", 0.8),
            
            # Bills & Utilities
            (["electricity", "water", "gas", "internet", "broadband", "mobile", "phone"], 
             "Bills & Utilities", 0.9),
            
            # Entertainment
            (["netflix", "spotify", "prime video", "hotstar", "movie", "cinema"], 
             "Entertainment", 0.9),
            
            # Health & Wellness
            (["pharmacy", "medical", "doctor", "hospital", "clinic", "medicine", "lab", "labs", "test", "covid", "diagnostic", "scan", "xray", "x-ray"], 
             "Health & Wellness", 0.85),
            (["gym", "fitness", "yoga"], 
             "Health & Wellness", 0.8),
        ]
        
        # Check each rule
        for keywords, category_name, confidence in rules:
            if any(keyword in merchant_lower for keyword in keywords):
                # Find category in database
                all_categories = await categories_crud.get_categories(supabase, 0, 1000)
                for cat in all_categories:
                    if cat.name == category_name:
                        return cat.category_id, cat.name, confidence
        
        # No rule matched
        return None, None, 0.0
    
    async def store_transaction_embedding(
        self,
        transaction_id: uuid.UUID,
        transaction_text: str,
        category_id: uuid.UUID,
        category_name: str,
        confidence_score: Optional[float] = None
    ) -> uuid.UUID:
        """
        Store or update transaction embedding in the database
        """
        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(transaction_text)
        
        # Convert to PostgreSQL array format
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # Upsert the embedding
        try:
            result = supabase.rpc(
                "upsert_transaction_embedding",
                {
                    "p_transaction_id": str(transaction_id),
                    "p_transaction_text": transaction_text,
                    "p_embedding": embedding_str,
                    "p_category_id": str(category_id),
                    "p_category_name": category_name,
                    "p_confidence_score": confidence_score
                }
            ).execute()
            
            return uuid.UUID(result.data) if result.data else None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to upsert transaction embedding: {str(e)}")
            logger.error(f"Transaction ID: {transaction_id}, Category: {category_name}")
            raise
    
    async def learn_from_feedback(
        self,
        transaction: TransactionResponse,
        confirmed_category_id: uuid.UUID,
        confirmed_category_name: str,
        description: Optional[str] = None
    ):
        """
        Update embeddings based on user feedback
        """
        # Format transaction text with confirmed category
        transaction_text = self.embedding_service.format_transaction_text(
            date=transaction.date,
            amount=transaction.amount,
            merchant=transaction.merchant,
            description=description,
            category=confirmed_category_name
        )
        
        # Store the embedding with confirmed category
        await self.store_transaction_embedding(
            transaction_id=transaction.transaction_id,
            transaction_text=transaction_text,
            category_id=confirmed_category_id,
            category_name=confirmed_category_name,
            confidence_score=1.0  # User confirmed = 100% confidence
        )