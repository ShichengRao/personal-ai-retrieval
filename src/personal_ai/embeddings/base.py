"""Base embedding service interface."""

from abc import ABC, abstractmethod
from typing import List, Union


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding lists
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get the dimension of embeddings produced by this service."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the embedding model."""
        pass