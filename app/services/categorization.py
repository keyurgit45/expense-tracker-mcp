"""
Intelligent transaction categorization service using embeddings and rules
"""
import json
from typing import List, Optional, Tuple, Dict
from decimal import Decimal
from datetime import datetime
import uuid

from app.database import supabase
from app.services.embeddings import EmbeddingService
from app.crud import categories as categories_crud
from app.schemas.schemas import TransactionResponse


class CategorizationService:
    """Service for intelligent transaction categorization"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
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
        result = supabase.rpc(
            "find_similar_transactions",
            {
                "query_embedding": embedding_str,
                "limit_count": limit,
                "similarity_threshold": self.similarity_threshold
            }
        ).execute()
        
        return result.data if result.data else []
    
    async def categorize_transaction(
        self,
        transaction: TransactionResponse,
        description: Optional[str] = None
    ) -> Tuple[Optional[uuid.UUID], Optional[str], float]:
        """
        Categorize a transaction using similarity search and LLM
        
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
            # No similar transactions found
            return None, None, 0.0
        
        # Check if we have high confidence based on similarity
        if similar_transactions[0]["similarity_score"] >= 0.9:
            # Very similar transaction found, use its category
            return (
                similar_transactions[0]["confirmed_category_id"],
                similar_transactions[0]["confirmed_category_name"],
                similar_transactions[0]["similarity_score"]
            )
        
        # Prepare examples for few-shot prompting
        examples = [
            (tx["transaction_text"], tx["confirmed_category_name"])
            for tx in similar_transactions
        ]
        
        # Get available categories
        all_categories = await categories_crud.get_categories(supabase, 0, 1000)
        category_names = [cat.name for cat in all_categories]
        
        # Generate few-shot prompt
        prompt = self.embedding_service.format_few_shot_prompt(
            new_transaction_text=transaction_text,
            similar_examples=examples,
            available_categories=category_names
        )
        
        # Call LLM for categorization
        try:
            import openai
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial categorization assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            predicted_category = response.choices[0].message.content.strip()
            
            # Find the category ID
            for cat in all_categories:
                if cat.name.lower() == predicted_category.lower():
                    # Calculate confidence based on similarity scores
                    avg_similarity = sum(tx["similarity_score"] for tx in similar_transactions) / len(similar_transactions)
                    return cat.category_id, cat.name, avg_similarity
            
            # Category not found
            return None, None, 0.0
            
        except Exception as e:
            print(f"LLM categorization failed: {str(e)}")
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