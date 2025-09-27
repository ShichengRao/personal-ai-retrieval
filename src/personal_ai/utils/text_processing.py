"""Text processing utilities for chunking and preprocessing."""

import re
from typing import List, Dict, Any, Optional
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TextChunker:
    """Text chunking utility for splitting documents into manageable pieces."""
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        max_tokens: Optional[int] = None
    ):
        """Initialize text chunker.
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            max_tokens: Maximum tokens per chunk (approximate)
        """
        self.chunk_size = chunk_size or config.get('text_processing.chunk_size', 1000)
        self.chunk_overlap = chunk_overlap or config.get('text_processing.chunk_overlap', 200)
        self.max_tokens = max_tokens or config.get('text_processing.max_tokens_per_chunk', 8000)
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to include with each chunk
            
        Returns:
            List of chunk dictionaries
        """
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Split into chunks
        chunks = self._split_text(cleaned_text)
        
        # Create chunk objects with metadata
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            chunk_metadata = {
                'chunk_index': i,
                'chunk_count': len(chunks),
                'chunk_size': len(chunk),
                'chunk_tokens': self._estimate_tokens(chunk)
            }
            
            # Add original metadata
            if metadata:
                chunk_metadata.update(metadata)
            
            chunk_objects.append({
                'text': chunk.strip(),
                'metadata': chunk_metadata
            })
        
        logger.debug(f"Split text into {len(chunk_objects)} chunks")
        return chunk_objects
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks using smart splitting.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to find a good split point
            split_point = self._find_split_point(text, start, end)
            
            if split_point == -1:
                # No good split point found, use hard split
                split_point = end
            
            chunk = text[start:split_point]
            chunks.append(chunk)
            
            # Move start position with overlap
            start = split_point - self.chunk_overlap
            if start < 0:
                start = 0
        
        return chunks
    
    def _find_split_point(self, text: str, start: int, end: int) -> int:
        """Find a good point to split text.
        
        Args:
            text: Full text
            start: Start position
            end: Preferred end position
            
        Returns:
            Best split point or -1 if none found
        """
        # Look for split points in order of preference
        search_start = max(start, end - 200)  # Don't search too far back
        
        # 1. Double newline (paragraph break)
        for i in range(end - 1, search_start - 1, -1):
            if text[i:i+2] == '\n\n':
                return i + 2
        
        # 2. Single newline
        for i in range(end - 1, search_start - 1, -1):
            if text[i] == '\n':
                return i + 1
        
        # 3. Sentence ending
        sentence_endings = ['. ', '! ', '? ']
        for i in range(end - 1, search_start - 1, -1):
            for ending in sentence_endings:
                if text[i:i+len(ending)] == ending:
                    return i + len(ending)
        
        # 4. Word boundary
        for i in range(end - 1, search_start - 1, -1):
            if text[i] == ' ':
                return i + 1
        
        return -1
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate number of tokens in text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4


class TextPreprocessor:
    """Text preprocessing utilities."""
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text.
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction based on word frequency
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words and count frequency
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:max_keywords]]
    
    @staticmethod
    def extract_entities(text: str) -> Dict[str, List[str]]:
        """Extract named entities from text (simple regex-based).
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of entity types and their values
        """
        entities = {
            'emails': [],
            'urls': [],
            'dates': [],
            'times': [],
            'phone_numbers': []
        }
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        entities['urls'] = re.findall(url_pattern, text)
        
        # Dates (simple patterns)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
            r'\b\d{1,2}-\d{1,2}-\d{4}\b'   # MM-DD-YYYY
        ]
        for pattern in date_patterns:
            entities['dates'].extend(re.findall(pattern, text))
        
        # Times
        time_pattern = r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b'
        entities['times'] = re.findall(time_pattern, text)
        
        # Phone numbers (simple pattern)
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        entities['phone_numbers'] = re.findall(phone_pattern, text)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    @staticmethod
    def summarize_text(text: str, max_sentences: int = 3) -> str:
        """Create a simple extractive summary.
        
        Args:
            text: Input text
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summary text
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return text
        
        # Simple scoring based on sentence length and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            # Score based on length (prefer medium-length sentences)
            length_score = min(len(sentence) / 100, 1.0)
            
            # Score based on position (prefer early sentences)
            position_score = 1.0 - (i / len(sentences))
            
            total_score = length_score + position_score
            scored_sentences.append((sentence, total_score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:max_sentences]]
        
        # Maintain original order
        summary_sentences = []
        for sentence in sentences:
            if sentence in top_sentences:
                summary_sentences.append(sentence)
                if len(summary_sentences) >= max_sentences:
                    break
        
        return '. '.join(summary_sentences) + '.'