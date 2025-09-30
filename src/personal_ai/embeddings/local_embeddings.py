"""Local embedding service using sentence-transformers."""

from typing import List, Optional
from sentence_transformers import SentenceTransformer

from .base import EmbeddingService
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class LocalEmbeddings(EmbeddingService):
    """Local embedding service using sentence-transformers."""
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """Initialize local embeddings service.
        
        Args:
            model_name: Model name. If None, uses config value
            device: Device to run on ('cpu', 'cuda'). If None, uses config value
        """
        self._model_name = model_name or config.local_embedding_model
        self.device = device or config.get('local_embeddings.device', 'cpu')
        
        logger.info(f"Loading local embedding model: {self._model_name} on {self.device}")
        
        try:
            self.model = SentenceTransformer(self._model_name, device=self.device)
            logger.info(f"Successfully loaded model with dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Error loading local embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating local embedding: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding lists
        """
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating local embeddings: {e}")
            raise
    
    @property
    def dimension(self) -> int:
        """Get the dimension of embeddings produced by this service."""
        return self.model.get_sentence_embedding_dimension()
    
    @property
    def model_name(self) -> str:
        """Get the name of the embedding model."""
        return self._model_name