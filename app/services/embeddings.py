"""
Embedding service for transaction categorization using OpenAI embeddings
"""
import os
from typing import List, Optional, Tuple
import openai
from decimal import Decimal
from datetime import datetime

from app.config import settings


class EmbeddingService:
    """Service for generating and managing transaction embeddings"""
    
    def __init__(self):
        """Initialize the embedding service with OpenAI API key"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        openai.api_key = self.api_key
        self.model = "text-embedding-ada-002"
        self.embedding_dimension = 1536
    
    def format_transaction_text(
        self,
        date: datetime,
        amount: Decimal,
        merchant: str,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> str:
        """
        Format transaction data into a standardized text representation
        
        Format: "YYYY-MM-DD│₹amount│merchant│description│category"
        """
        # Format date
        date_str = date.strftime("%Y-%m-%d")
        
        # Format amount with currency symbol
        amount_str = f"₹{float(amount)}"
        
        # Clean merchant name
        merchant_str = merchant.strip() if merchant else "Unknown"
        
        # Include description if available
        desc_str = description.strip() if description else ""
        
        # Build the text representation
        parts = [date_str, amount_str, merchant_str]
        
        if desc_str:
            parts.append(desc_str)
        
        # Add category if provided (for training data)
        if category:
            parts.append(f"→ {category}")
        
        return "│".join(parts)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text using OpenAI API
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = await openai.Embedding.acreate(
                model=self.model,
                input=text
            )
            return response["data"][0]["embedding"]
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Returns:
            Similarity score between 0 and 1 (1 being identical)
        """
        # This is handled by pgvector in the database
        # This method is for reference/testing only
        import numpy as np
        
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def format_few_shot_prompt(
        self,
        new_transaction_text: str,
        similar_examples: List[Tuple[str, str]],
        available_categories: List[str]
    ) -> str:
        """
        Format a few-shot prompt for the LLM to categorize a transaction
        
        Args:
            new_transaction_text: The new transaction to categorize
            similar_examples: List of (transaction_text, category) tuples
            available_categories: List of valid category names
            
        Returns:
            Formatted prompt string
        """
        prompt = """You are a personal finance assistant specializing in expense categorization for Indian users.

Based on the similar past transactions below, categorize the new transaction.

Similar past transactions:
"""
        
        # Add examples
        for i, (tx_text, category) in enumerate(similar_examples, 1):
            prompt += f"{i}. {tx_text}\n"
        
        prompt += f"\nNow categorize this new transaction:\n{new_transaction_text}\n\n"
        prompt += f"Available categories: {', '.join(available_categories)}\n\n"
        prompt += "Respond with ONLY the category name, nothing else."
        
        return prompt
    
    def extract_transaction_details(self, transaction_text: str) -> dict:
        """
        Extract transaction details from formatted text
        
        Returns dict with: date, amount, merchant, description
        """
        parts = transaction_text.split("│")
        
        details = {
            "date": parts[0] if len(parts) > 0 else None,
            "amount": parts[1].replace("₹", "") if len(parts) > 1 else None,
            "merchant": parts[2] if len(parts) > 2 else None,
            "description": parts[3] if len(parts) > 3 and "→" not in parts[3] else None,
        }
        
        # Extract category if present
        for part in parts:
            if "→" in part:
                details["category"] = part.split("→")[1].strip()
                break
        
        return details