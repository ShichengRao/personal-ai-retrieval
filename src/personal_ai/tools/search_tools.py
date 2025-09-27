"""Search-related tools for AI actions."""

from typing import Dict, Any, List, Optional

from .base import BaseTool
from ..query.semantic_search import SemanticSearch
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SearchDocumentsTool(BaseTool):
    """Tool for searching indexed documents."""
    
    def __init__(self, search_engine: Optional[SemanticSearch] = None):
        """Initialize document search tool.
        
        Args:
            search_engine: Semantic search engine instance
        """
        self.search_engine = search_engine or SemanticSearch()
    
    @property
    def name(self) -> str:
        return "search_documents"
    
    @property
    def description(self) -> str:
        return "Search through indexed documents (local files, emails, calendar events) using semantic similarity."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Search query to find relevant documents"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "default": 5
            },
            "source_filter": {
                "type": "string",
                "description": "Filter by document source (e.g., 'gmail', 'google_calendar', 'local_file', 'google_drive')",
                "default": ""
            },
            "similarity_threshold": {
                "type": "number",
                "description": "Minimum similarity score (0.0 to 1.0, default: 0.7)",
                "default": 0.7
            }
        }
    
    def execute(
        self,
        query: str,
        max_results: int = 5,
        source_filter: str = "",
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Search documents.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            source_filter: Source filter
            similarity_threshold: Minimum similarity score
            
        Returns:
            Search results
        """
        try:
            # Build filters
            filters = {}
            if source_filter:
                filters['source'] = source_filter
            
            # Perform search
            results = self.search_engine.search(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                filters=filters if filters else None
            )
            
            # Format results for LLM consumption
            formatted_results = []
            for result in results:
                formatted_result = {
                    'title': result.get('title', 'Untitled'),
                    'content_preview': result.get('content', '')[:300] + "..." if len(result.get('content', '')) > 300 else result.get('content', ''),
                    'source': result.get('source', 'unknown'),
                    'similarity': result.get('similarity', 0.0),
                    'url': result.get('url', ''),
                    'date': result.get('date', '')
                }
                
                # Add source-specific metadata
                metadata = result.get('metadata', {})
                if result.get('source') == 'gmail':
                    formatted_result['from'] = metadata.get('from', '')
                    formatted_result['subject'] = metadata.get('subject', '')
                elif result.get('source') == 'google_calendar':
                    formatted_result['start_time'] = metadata.get('start_time', '')
                    formatted_result['location'] = metadata.get('location', '')
                elif result.get('source') == 'local_file':
                    formatted_result['file_path'] = metadata.get('path', '')
                    formatted_result['file_type'] = metadata.get('extension', '')
                
                formatted_results.append(formatted_result)
            
            return {
                'results': formatted_results,
                'count': len(formatted_results),
                'query': query,
                'source_filter': source_filter or 'all sources'
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return {
                'error': str(e),
                'results': [],
                'count': 0
            }


class FindSimilarDocumentsTool(BaseTool):
    """Tool for finding documents similar to a given document."""
    
    def __init__(self, search_engine: Optional[SemanticSearch] = None):
        """Initialize similar documents tool.
        
        Args:
            search_engine: Semantic search engine instance
        """
        self.search_engine = search_engine or SemanticSearch()
    
    @property
    def name(self) -> str:
        return "find_similar_documents"
    
    @property
    def description(self) -> str:
        return "Find documents similar to a given document ID. Useful for finding related content."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "document_id": {
                "type": "string",
                "description": "ID of the reference document to find similar documents for"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of similar documents to return (default: 5)",
                "default": 5
            },
            "similarity_threshold": {
                "type": "number",
                "description": "Minimum similarity score (0.0 to 1.0, default: 0.5)",
                "default": 0.5
            }
        }
    
    def execute(
        self,
        document_id: str,
        max_results: int = 5,
        similarity_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Find similar documents.
        
        Args:
            document_id: Reference document ID
            max_results: Maximum results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            Similar documents
        """
        try:
            results = self.search_engine.find_similar_documents(
                document_id=document_id,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'title': result.get('title', 'Untitled'),
                    'content_preview': result.get('content', '')[:200] + "..." if len(result.get('content', '')) > 200 else result.get('content', ''),
                    'source': result.get('source', 'unknown'),
                    'similarity': result.get('similarity', 0.0),
                    'url': result.get('url', ''),
                    'date': result.get('date', '')
                })
            
            return {
                'similar_documents': formatted_results,
                'count': len(formatted_results),
                'reference_document_id': document_id
            }
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return {
                'error': str(e),
                'similar_documents': [],
                'count': 0
            }


class SearchBySourceTool(BaseTool):
    """Tool for searching documents by source type."""
    
    def __init__(self, search_engine: Optional[SemanticSearch] = None):
        """Initialize source search tool.
        
        Args:
            search_engine: Semantic search engine instance
        """
        self.search_engine = search_engine or SemanticSearch()
    
    @property
    def name(self) -> str:
        return "search_by_source"
    
    @property
    def description(self) -> str:
        return "Search documents filtered by source type (gmail, calendar, local files, etc.)."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "source": {
                "type": "string",
                "description": "Source type to search in ('gmail', 'google_calendar', 'local_file', 'google_drive')"
            },
            "query": {
                "type": "string",
                "description": "Search query (optional - if empty, returns recent documents from source)",
                "default": ""
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 10)",
                "default": 10
            }
        }
    
    def execute(
        self,
        source: str,
        query: str = "",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Search by source.
        
        Args:
            source: Source type to search
            query: Optional search query
            max_results: Maximum results to return
            
        Returns:
            Search results from specified source
        """
        try:
            filters = {'source': source}
            
            if query:
                # Semantic search with source filter
                results = self.search_engine.search(
                    query=query,
                    max_results=max_results,
                    filters=filters
                )
            else:
                # Just get documents from source
                results = self.search_engine.search_by_filters(
                    filters=filters,
                    max_results=max_results
                )
            
            # Format results based on source type
            formatted_results = []
            for result in results:
                base_result = {
                    'title': result.get('title', 'Untitled'),
                    'content_preview': result.get('content', '')[:300] + "..." if len(result.get('content', '')) > 300 else result.get('content', ''),
                    'source': result.get('source', 'unknown'),
                    'url': result.get('url', ''),
                    'date': result.get('date', '')
                }
                
                if query:
                    base_result['similarity'] = result.get('similarity', 0.0)
                
                # Add source-specific fields
                metadata = result.get('metadata', {})
                if source == 'gmail':
                    base_result.update({
                        'from': metadata.get('from', ''),
                        'to': metadata.get('to', ''),
                        'subject': metadata.get('subject', '')
                    })
                elif source == 'google_calendar':
                    base_result.update({
                        'start_time': metadata.get('start_time', ''),
                        'end_time': metadata.get('end_time', ''),
                        'location': metadata.get('location', ''),
                        'attendees': metadata.get('attendees', [])
                    })
                elif source == 'local_file':
                    base_result.update({
                        'file_path': metadata.get('path', ''),
                        'file_type': metadata.get('extension', ''),
                        'file_size': metadata.get('size', 0)
                    })
                elif source == 'google_drive':
                    base_result.update({
                        'mime_type': metadata.get('mime_type', ''),
                        'owners': metadata.get('owners', [])
                    })
                
                formatted_results.append(base_result)
            
            return {
                'results': formatted_results,
                'count': len(formatted_results),
                'source': source,
                'query': query or 'all documents'
            }
            
        except Exception as e:
            logger.error(f"Error searching by source: {e}")
            return {
                'error': str(e),
                'results': [],
                'count': 0
            }