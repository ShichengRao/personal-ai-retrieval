"""ChromaDB manager for vector storage and retrieval."""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings

from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ChromaManager:
    """Manager for ChromaDB vector database operations."""
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """Initialize ChromaDB manager.
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory or config.vector_db_path
        self.collection_name = collection_name or config.vector_db_collection
        
        # Create persist directory if it doesn't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Personal AI document embeddings"}
        )
        
        logger.info(f"Initialized ChromaDB at {self.persist_directory}")
        logger.info(f"Collection '{self.collection_name}' has {self.collection.count()} documents")
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents to the collection.
        
        Args:
            texts: List of document texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs. If None, UUIDs will be generated
            
        Returns:
            List of document IDs
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        if len(texts) != len(embeddings) != len(metadatas) != len(ids):
            raise ValueError("All input lists must have the same length")
        
        try:
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(texts)} documents to collection")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}")
            raise
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Query the collection for similar documents.
        
        Args:
            query_embeddings: List of query embedding vectors
            n_results: Number of results to return per query
            where: Optional metadata filter
            include: What to include in results ('documents', 'metadatas', 'distances')
            
        Returns:
            Query results dictionary
        """
        if include is None:
            include = ['documents', 'metadatas', 'distances']
        
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                include=include
            )
            logger.debug(f"Query returned {len(results.get('ids', []))} results")
            return results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            raise
    
    def get_documents(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get documents from the collection.
        
        Args:
            ids: Optional list of document IDs to retrieve
            where: Optional metadata filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            include: What to include in results
            
        Returns:
            Documents dictionary
        """
        if include is None:
            include = ['documents', 'metadatas']
        
        try:
            results = self.collection.get(
                ids=ids,
                where=where,
                limit=limit,
                offset=offset,
                include=include
            )
            logger.debug(f"Retrieved {len(results.get('ids', []))} documents")
            return results
        except Exception as e:
            logger.error(f"Error getting documents from ChromaDB: {e}")
            raise
    
    def update_documents(
        self,
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None
    ) -> None:
        """Update existing documents in the collection.
        
        Args:
            ids: List of document IDs to update
            embeddings: Optional new embeddings
            metadatas: Optional new metadata
            documents: Optional new document texts
        """
        try:
            self.collection.update(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Updated {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error updating documents in ChromaDB: {e}")
            raise
    
    def delete_documents(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> None:
        """Delete documents from the collection.
        
        Args:
            ids: Optional list of document IDs to delete
            where: Optional metadata filter for deletion
        """
        try:
            self.collection.delete(ids=ids, where=where)
            logger.info(f"Deleted documents from collection")
        except Exception as e:
            logger.error(f"Error deleting documents from ChromaDB: {e}")
            raise
    
    def count(self) -> int:
        """Get the number of documents in the collection.
        
        Returns:
            Number of documents
        """
        return self.collection.count()
    
    def clear(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Personal AI document embeddings"}
            )
            logger.info("Cleared all documents from collection")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise
    
    def document_exists(self, doc_id: str) -> bool:
        """Check if a document exists in the collection.
        
        Args:
            doc_id: Document ID to check
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            result = self.collection.get(ids=[doc_id], include=[])
            return len(result['ids']) > 0
        except Exception:
            return False