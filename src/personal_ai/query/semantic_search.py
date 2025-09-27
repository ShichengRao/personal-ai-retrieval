"""Semantic search engine using vector similarity."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from ..embeddings.factory import get_default_embedding_service
from ..storage.chroma_manager import ChromaManager
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SemanticSearch:
    """Semantic search engine for querying documents."""
    
    def __init__(
        self,
        embedding_service=None,
        vector_db=None
    ):
        """Initialize semantic search engine.
        
        Args:
            embedding_service: Embedding service instance
            vector_db: Vector database instance
        """
        self.embedding_service = embedding_service or get_default_embedding_service()
        self.vector_db = vector_db or ChromaManager()
        
        logger.info("Initialized semantic search engine")
    
    def search(
        self,
        query: str,
        max_results: int = None,
        similarity_threshold: float = None,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for documents similar to the query.
        
        Args:
            query: Search query text
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            filters: Optional metadata filters
            include_metadata: Whether to include document metadata
            
        Returns:
            List of search results with scores and metadata
        """
        max_results = max_results or config.get('query.max_results', 10)
        similarity_threshold = similarity_threshold or config.get('query.similarity_threshold', 0.7)
        
        logger.info(f"Searching for: '{query}' (max_results={max_results}, threshold={similarity_threshold})")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            
            # Search vector database
            include_fields = ['documents', 'metadatas', 'distances']
            if not include_metadata:
                include_fields = ['documents', 'distances']
            
            results = self.vector_db.query(
                query_embeddings=[query_embedding],
                n_results=max_results * 2,  # Get more results to filter by threshold
                where=filters,
                include=include_fields
            )
            
            # Process results
            search_results = self._process_search_results(
                results,
                similarity_threshold,
                max_results,
                include_metadata
            )
            
            logger.info(f"Found {len(search_results)} results above threshold")
            return search_results
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            raise
    
    def _process_search_results(
        self,
        raw_results: Dict[str, Any],
        similarity_threshold: float,
        max_results: int,
        include_metadata: bool
    ) -> List[Dict[str, Any]]:
        """Process raw search results from vector database.
        
        Args:
            raw_results: Raw results from ChromaDB
            similarity_threshold: Minimum similarity score
            max_results: Maximum number of results
            include_metadata: Whether to include metadata
            
        Returns:
            Processed search results
        """
        if not raw_results.get('ids') or not raw_results['ids'][0]:
            return []
        
        # Extract data from first query results
        ids = raw_results['ids'][0]
        documents = raw_results.get('documents', [[]])[0]
        distances = raw_results.get('distances', [[]])[0]
        metadatas = raw_results.get('metadatas', [[]])[0] if include_metadata else [{}] * len(ids)
        
        results = []
        
        for i, (doc_id, document, distance, metadata) in enumerate(zip(ids, documents, distances, metadatas)):
            # Convert distance to similarity score (ChromaDB uses cosine distance)
            similarity = 1.0 - distance
            
            # Filter by similarity threshold
            if similarity < similarity_threshold:
                continue
            
            result = {
                'id': doc_id,
                'content': document,
                'similarity': similarity,
                'rank': len(results) + 1
            }
            
            if include_metadata and metadata:
                result['metadata'] = metadata
                
                # Extract useful fields from metadata
                result['source'] = metadata.get('source', 'unknown')
                result['source_id'] = metadata.get('source_id', doc_id)
                result['title'] = metadata.get('name') or metadata.get('subject') or metadata.get('summary', '')
                result['url'] = metadata.get('url', '')
                result['date'] = metadata.get('date') or metadata.get('modified_time') or metadata.get('created_time', '')
            
            results.append(result)
            
            # Stop if we have enough results
            if len(results) >= max_results:
                break
        
        return results
    
    def search_by_filters(
        self,
        filters: Dict[str, Any],
        max_results: int = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Search documents by metadata filters only.
        
        Args:
            filters: Metadata filters
            max_results: Maximum number of results
            include_metadata: Whether to include metadata
            
        Returns:
            List of matching documents
        """
        max_results = max_results or config.get('query.max_results', 10)
        
        logger.info(f"Searching by filters: {filters}")
        
        try:
            include_fields = ['documents', 'metadatas'] if include_metadata else ['documents']
            
            results = self.vector_db.get_documents(
                where=filters,
                limit=max_results,
                include=include_fields
            )
            
            # Process results
            search_results = []
            
            if results.get('ids'):
                ids = results['ids']
                documents = results.get('documents', [])
                metadatas = results.get('metadatas', []) if include_metadata else [{}] * len(ids)
                
                for i, (doc_id, document, metadata) in enumerate(zip(ids, documents, metadatas)):
                    result = {
                        'id': doc_id,
                        'content': document,
                        'similarity': 1.0,  # No similarity calculation for filter-only search
                        'rank': i + 1
                    }
                    
                    if include_metadata and metadata:
                        result['metadata'] = metadata
                        result['source'] = metadata.get('source', 'unknown')
                        result['source_id'] = metadata.get('source_id', doc_id)
                        result['title'] = metadata.get('name') or metadata.get('subject') or metadata.get('summary', '')
                        result['url'] = metadata.get('url', '')
                        result['date'] = metadata.get('date') or metadata.get('modified_time') or metadata.get('created_time', '')
                    
                    search_results.append(result)
            
            logger.info(f"Found {len(search_results)} results matching filters")
            return search_results
            
        except Exception as e:
            logger.error(f"Error during filter search: {e}")
            raise
    
    def find_similar_documents(
        self,
        document_id: str,
        max_results: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Find documents similar to a given document.
        
        Args:
            document_id: ID of the reference document
            max_results: Maximum number of similar documents to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar documents
        """
        try:
            # Get the reference document
            doc_results = self.vector_db.get_documents(
                ids=[document_id],
                include=['documents', 'metadatas']
            )
            
            if not doc_results.get('ids') or not doc_results['ids']:
                logger.warning(f"Document not found: {document_id}")
                return []
            
            reference_doc = doc_results['documents'][0]
            
            # Use the document content as query
            return self.search(
                query=reference_doc,
                max_results=max_results + 1,  # +1 to account for the reference document itself
                similarity_threshold=similarity_threshold
            )[1:]  # Exclude the reference document from results
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            raise
    
    def get_search_suggestions(self, partial_query: str, max_suggestions: int = 5) -> List[str]:
        """Get search suggestions based on partial query.
        
        Args:
            partial_query: Partial search query
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested queries
        """
        # This is a simple implementation - could be enhanced with more sophisticated methods
        try:
            if len(partial_query) < 3:
                return []
            
            # Search for documents containing the partial query
            results = self.search(
                query=partial_query,
                max_results=max_suggestions * 2,
                similarity_threshold=0.3
            )
            
            suggestions = []
            for result in results:
                content = result.get('content', '')
                title = result.get('title', '')
                
                # Extract phrases containing the partial query
                import re
                pattern = rf'\b\w*{re.escape(partial_query)}\w*\b'
                
                matches = re.findall(pattern, content + ' ' + title, re.IGNORECASE)
                for match in matches:
                    if match.lower() not in [s.lower() for s in suggestions]:
                        suggestions.append(match)
                        if len(suggestions) >= max_suggestions:
                            break
                
                if len(suggestions) >= max_suggestions:
                    break
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []