"""Claude-based text analysis service.

Note: Claude doesn't provide embeddings API, so this service uses Claude for text analysis
and preprocessing, but relies on local embeddings for vector generation.
"""

from typing import List, Optional
import anthropic

from .local_embeddings import LocalEmbeddings
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ClaudeEmbeddings(LocalEmbeddings):
    """Claude-enhanced embedding service that uses Claude for text preprocessing."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: Optional[str] = None,
        local_model: Optional[str] = None
    ):
        """Initialize Claude embeddings service.
        
        Args:
            api_key: Claude API key. If None, uses config value
            model: Claude model name. If None, uses config value
            local_model: Local embedding model name for vector generation
        """
        self.api_key = api_key or config.get('claude.api_key')
        self.claude_model = model or config.get('claude.model', 'claude-3-5-sonnet-20241022')
        
        # Initialize local embeddings for vector generation
        super().__init__(model_name=local_model)
        
        # Initialize Claude client if API key is available
        self.claude_client = None
        if self.api_key:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"Initialized Claude client with model: {self.claude_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Claude client: {e}")
                self.claude_client = None
        else:
            logger.info("No Claude API key provided, using local embeddings only")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text with Claude preprocessing.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        # Preprocess text with Claude if available
        processed_text = self._preprocess_with_claude(text)
        
        # Generate embedding using local model
        return super().embed_text(processed_text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts with Claude preprocessing.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding lists
        """
        # Preprocess texts with Claude if available
        processed_texts = [self._preprocess_with_claude(text) for text in texts]
        
        # Generate embeddings using local model
        return super().embed_texts(processed_texts)
    
    def _preprocess_with_claude(self, text: str) -> str:
        """Preprocess text using Claude for better embedding quality.
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        if not self.claude_client or len(text) < 100:
            # Skip preprocessing for short texts or if Claude is not available
            return text
        
        try:
            # Use Claude to extract key information and clean up text
            prompt = f"""Please analyze the following text and extract the key information, concepts, and topics. 
            Rewrite it in a clear, concise way that preserves all important semantic meaning while removing noise.
            Focus on the main ideas, entities, and relationships.

            Text to analyze:
            {text}

            Provide only the cleaned and enhanced version:"""
            
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=min(len(text) * 2, 1000),  # Reasonable limit
                messages=[{"role": "user", "content": prompt}]
            )
            
            processed_text = response.content[0].text.strip()
            
            # Fallback to original if processing failed
            if len(processed_text) < len(text) * 0.3:  # Too much reduction
                logger.debug("Claude preprocessing reduced text too much, using original")
                return text
            
            logger.debug(f"Claude preprocessing: {len(text)} -> {len(processed_text)} chars")
            return processed_text
            
        except Exception as e:
            logger.debug(f"Claude preprocessing failed: {e}, using original text")
            return text
    
    @property
    def model_name(self) -> str:
        """Get the name of the embedding model."""
        if self.claude_client:
            return f"claude-enhanced-{super().model_name}"
        else:
            return super().model_name
    
    def analyze_text_with_claude(self, text: str, analysis_type: str = "summary") -> str:
        """Use Claude for text analysis tasks.
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis ('summary', 'keywords', 'entities', 'topics')
            
        Returns:
            Analysis result
        """
        if not self.claude_client:
            logger.warning("Claude client not available for text analysis")
            return ""
        
        try:
            prompts = {
                "summary": f"Provide a concise summary of the following text:\n\n{text}",
                "keywords": f"Extract the most important keywords and phrases from this text:\n\n{text}",
                "entities": f"Identify and list all named entities (people, places, organizations, dates, etc.) in this text:\n\n{text}",
                "topics": f"Identify the main topics and themes discussed in this text:\n\n{text}"
            }
            
            prompt = prompts.get(analysis_type, prompts["summary"])
            
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Claude text analysis failed: {e}")
            return ""