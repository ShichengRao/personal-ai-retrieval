"""Embedding service factory for automatic fallback."""

from typing import Optional

from .base import EmbeddingService
from .openai_embeddings import OpenAIEmbeddings
from .local_embeddings import LocalEmbeddings
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


def create_embedding_service(
    prefer_openai: bool = True,
    openai_api_key: Optional[str] = None,
    local_model: Optional[str] = None
) -> EmbeddingService:
    """Create an embedding service with automatic fallback.
    
    Args:
        prefer_openai: Whether to prefer OpenAI over local models
        openai_api_key: OpenAI API key override
        local_model: Local model name override
        
    Returns:
        EmbeddingService instance
    """
    # Try OpenAI first if preferred and API key is available
    if prefer_openai:
        api_key = openai_api_key or config.openai_api_key
        if api_key:
            try:
                logger.info("Attempting to use OpenAI embeddings")
                return OpenAIEmbeddings(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
                logger.info("Falling back to local embeddings")
    
    # Fall back to local embeddings
    try:
        logger.info("Using local embeddings")
        return LocalEmbeddings(model_name=local_model)
    except Exception as e:
        logger.error(f"Failed to initialize local embeddings: {e}")
        raise RuntimeError("Could not initialize any embedding service")


def get_default_embedding_service() -> EmbeddingService:
    """Get the default embedding service based on configuration.
    
    Returns:
        EmbeddingService instance
    """
    return create_embedding_service()