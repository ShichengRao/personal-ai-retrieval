"""LLM client factory for automatic selection."""

from typing import Optional

from .base import BaseLLMClient
from .claude_client import ClaudeLLMClient
from .openai_client import OpenAILLMClient
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


def create_llm_client(
    prefer_claude: bool = False,
    prefer_openai: bool = True,
    claude_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> Optional[BaseLLMClient]:
    """Create an LLM client with automatic fallback.
    
    Args:
        prefer_claude: Whether to prefer Claude over OpenAI
        prefer_openai: Whether to prefer OpenAI over Claude
        claude_api_key: Claude API key override
        openai_api_key: OpenAI API key override
        
    Returns:
        LLM client instance or None if no API keys available
    """
    # Try Claude first if preferred
    if prefer_claude:
        claude_key = claude_api_key or config.get('claude.api_key')
        if claude_key:
            try:
                logger.info("Attempting to use Claude LLM client")
                return ClaudeLLMClient(api_key=claude_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Claude client: {e}")
    
    # Try OpenAI if preferred or as fallback
    if prefer_openai:
        openai_key = openai_api_key or config.openai_api_key
        if openai_key:
            try:
                logger.info("Attempting to use OpenAI LLM client")
                return OpenAILLMClient(api_key=openai_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    # If Claude wasn't preferred initially, try it as fallback
    if not prefer_claude:
        claude_key = claude_api_key or config.get('claude.api_key')
        if claude_key:
            try:
                logger.info("Falling back to Claude LLM client")
                return ClaudeLLMClient(api_key=claude_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Claude client: {e}")
    
    logger.warning("No LLM API keys available")
    return None


def get_default_llm_client() -> Optional[BaseLLMClient]:
    """Get the default LLM client based on configuration.
    
    Returns:
        LLM client instance or None
    """
    # Check if user has a preference in config
    prefer_claude = config.get('llm.prefer_claude', False)
    prefer_openai = config.get('llm.prefer_openai', True)
    
    return create_llm_client(
        prefer_claude=prefer_claude,
        prefer_openai=prefer_openai
    )