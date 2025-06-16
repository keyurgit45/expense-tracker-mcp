"""
Free embedding service for transaction categorization using Sentence Transformers
"""
from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer


class FreeEmbeddingService:
    """Service for generating embeddings using free local models"""
    
    def __init__(self):
        """Initialize with a free, efficient model"""
        # This model is small (90MB) and works well for similarity search
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dimension = 384  # This model outputs 384 dimensions
    
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
        Generate embedding vector for the given text using local model
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Generate embedding (this runs locally, no API needed)
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Returns:
            Similarity score between 0 and 1 (1 being identical)
        """
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