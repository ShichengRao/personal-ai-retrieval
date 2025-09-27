"""OpenAI embedding service implementation."""

from typing import List, Optional
import openai
from openai import OpenAI

from .base import EmbeddingService
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIEmbeddings(EmbeddingService):
    """OpenAI embedding service using their API."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize OpenAI embeddings service.
        
        Args:
            api_key: OpenAI API key. If None, uses config value
            model: Model name. If None, uses config value
        """
        self.api_key = api_key or config.openai_api_key
        self.model = model or config.openai_embedding_model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI embeddings with model: {self.model}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding lists
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {e}")
            raise
    
    @property
    def dimension(self) -> int:
        """Get the dimension of embeddings produced by this service."""
        # OpenAI embedding dimensions by model
        dimensions = {
            'text-embedding-3-large': 3072,
            'text-embedding-3-small': 1536,
            'text-embedding-ada-002': 1536,
        }
        return dimensions.get(self.model, 1536)
    
    @property
    def model_name(self) -> str:
        """Get the name of the embedding model."""
        return self.model