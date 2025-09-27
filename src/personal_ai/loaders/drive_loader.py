"""Google Drive API loader for documents and files."""

import io
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .google_auth import GoogleAuthManager
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DriveLoader:
    """Loader for Google Drive documents using Google API."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize Drive loader.
        
        Args:
            auth_manager: Google authentication manager. If None, creates new one
        """
        self.auth_manager = auth_manager or GoogleAuthManager()
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize Drive API service."""
        try:
            credentials = self.auth_manager.get_credentials()
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Initialized Drive API service")
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}")
            raise
    
    def load_documents(
        self,
        file_types: Optional[List[str]] = None,
        max_files: int = 1000,
        include_shared: bool = True
    ) -> List[Dict[str, Any]]:
        """Load documents from Google Drive.
        
        Args:
            file_types: List of MIME types to include
            max_files: Maximum number of files to load
            include_shared: Whether to include shared files
            
        Returns:
            List of document dictionaries with metadata
        """
        if file_types is None:
            file_types = [
                'application/vnd.google-apps.document',  # Google Docs
                'application/vnd.google-apps.spreadsheet',  # Google Sheets
                'application/vnd.google-apps.presentation',  # Google Slides
                'application/pdf',  # PDF files
                'text/plain',  # Text files
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # XLSX
            ]
        
        logger.info(f"Loading Drive documents with types: {file_types}")
        
        try:
            documents = []
            page_token = None
            
            while len(documents) < max_files:
                # Build query
                query_parts = []
                if file_types:
                    mime_queries = [f"mimeType='{mime_type}'" for mime_type in file_types]
                    query_parts.append(f"({' or '.join(mime_queries)})")
                
                if not include_shared:
                    query_parts.append("'me' in owners")
                
                # Exclude trashed files
                query_parts.append("trashed=false")
                
                query = " and ".join(query_parts)
                
                results = self.service.files().list(
                    q=query,
                    pageSize=min(1000, max_files - len(documents)),
                    pageToken=page_token,
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, owners, parents, webViewLink, description)"
                ).execute()
                
                files = results.get('files', [])
                
                for file_info in files:
                    try:
                        doc_data = self._process_document(file_info)
                        if doc_data:
                            documents.append(doc_data)
                    except Exception as e:
                        logger.warning(f"Failed to process file {file_info.get('id')}: {e}")
                        continue
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Successfully loaded {len(documents)} Drive documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading Drive documents: {e}")
            raise
    
    def _process_document(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single Drive document.
        
        Args:
            file_info: File information from Drive API
            
        Returns:
            Processed document data or None if failed
        """
        try:
            file_id = file_info['id']
            mime_type = file_info['mimeType']
            
            # Extract text content based on file type
            content = self._extract_content(file_id, mime_type)
            
            if not content:
                logger.warning(f"No content extracted from file {file_id}")
                return None
            
            # Get owners information
            owners = []
            for owner in file_info.get('owners', []):
                owners.append({
                    'name': owner.get('displayName'),
                    'email': owner.get('emailAddress'),
                    'me': owner.get('me', False)
                })
            
            return {
                'id': file_id,
                'name': file_info.get('name', ''),
                'mime_type': mime_type,
                'content': content,
                'size': int(file_info.get('size', 0)) if file_info.get('size') else 0,
                'created_time': file_info.get('createdTime'),
                'modified_time': file_info.get('modifiedTime'),
                'owners': owners,
                'description': file_info.get('description', ''),
                'web_view_link': file_info.get('webViewLink'),
                'source': 'google_drive',
                'source_id': file_id,
                'url': file_info.get('webViewLink', '')
            }
            
        except Exception as e:
            logger.error(f"Error processing Drive document {file_info.get('id')}: {e}")
            return None
    
    def _extract_content(self, file_id: str, mime_type: str) -> str:
        """Extract text content from a Drive file.
        
        Args:
            file_id: Drive file ID
            mime_type: File MIME type
            
        Returns:
            Extracted text content
        """
        try:
            if mime_type == 'application/vnd.google-apps.document':
                # Google Docs - export as plain text
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                )
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Google Sheets - export as CSV
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='text/csv'
                )
            elif mime_type == 'application/vnd.google-apps.presentation':
                # Google Slides - export as plain text
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                )
            elif mime_type in ['text/plain', 'application/pdf']:
                # Direct download for text and PDF files
                request = self.service.files().get_media(fileId=file_id)
            else:
                # Try to export as plain text for other formats
                try:
                    request = self.service.files().export_media(
                        fileId=file_id,
                        mimeType='text/plain'
                    )
                except:
                    # Fall back to direct download
                    request = self.service.files().get_media(fileId=file_id)
            
            # Download content
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Decode content
            content = file_io.getvalue().decode('utf-8', errors='ignore')
            return content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting content from file {file_id}: {e}")
            return ""
    
    def search_files(
        self,
        query: str,
        max_results: int = 10,
        file_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search Drive files.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            file_types: Optional list of MIME types to filter
            
        Returns:
            List of matching files
        """
        try:
            # Build search query
            query_parts = [f"fullText contains '{query}'"]
            
            if file_types:
                mime_queries = [f"mimeType='{mime_type}'" for mime_type in file_types]
                query_parts.append(f"({' or '.join(mime_queries)})")
            
            query_parts.append("trashed=false")
            search_query = " and ".join(query_parts)
            
            results = self.service.files().list(
                q=search_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, owners, webViewLink, description)"
            ).execute()
            
            files = []
            for file_info in results.get('files', []):
                doc_data = self._process_document(file_info)
                if doc_data:
                    files.append(doc_data)
            
            logger.info(f"Found {len(files)} files matching query: {query}")
            return files
            
        except Exception as e:
            logger.error(f"Error searching Drive files: {e}")
            raise
    
    def get_file_content(self, file_id: str) -> Optional[str]:
        """Get content of a specific file.
        
        Args:
            file_id: Drive file ID
            
        Returns:
            File content or None if failed
        """
        try:
            # Get file metadata
            file_info = self.service.files().get(fileId=file_id).execute()
            mime_type = file_info.get('mimeType')
            
            return self._extract_content(file_id, mime_type)
            
        except Exception as e:
            logger.error(f"Error getting file content for {file_id}: {e}")
            return None