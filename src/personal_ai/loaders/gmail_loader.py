"""Gmail API loader for email ingestion."""

import base64
import email
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build

from .google_auth import GoogleAuthManager
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GmailLoader:
    """Loader for Gmail emails using Google API."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize Gmail loader.
        
        Args:
            auth_manager: Google authentication manager. If None, creates new one
        """
        self.auth_manager = auth_manager or GoogleAuthManager()
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize Gmail API service."""
        try:
            credentials = self.auth_manager.get_credentials()
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info("Initialized Gmail API service")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            raise
    
    def load_emails(
        self,
        max_emails: Optional[int] = None,
        days_back: Optional[int] = None,
        include_sent: bool = True,
        include_drafts: bool = False,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Load emails from Gmail.
        
        Args:
            max_emails: Maximum number of emails to load
            days_back: Number of days back to search
            include_sent: Whether to include sent emails
            include_drafts: Whether to include draft emails
            query: Custom Gmail search query
            
        Returns:
            List of email dictionaries with metadata
        """
        max_emails = max_emails or config.get('gmail.max_emails', 1000)
        days_back = days_back or config.get('gmail.days_back', 30)
        include_sent = include_sent if include_sent is not None else config.get('gmail.include_sent', True)
        include_drafts = include_drafts if include_drafts is not None else config.get('gmail.include_drafts', False)
        
        # Build search query
        search_query = self._build_search_query(
            days_back=days_back,
            include_sent=include_sent,
            include_drafts=include_drafts,
            custom_query=query
        )
        
        logger.info(f"Loading emails with query: {search_query}")
        
        try:
            # Get list of message IDs
            message_ids = self._get_message_ids(search_query, max_emails)
            logger.info(f"Found {len(message_ids)} emails to process")
            
            # Load email details
            emails = []
            for i, msg_id in enumerate(message_ids):
                try:
                    email_data = self._get_email_details(msg_id)
                    if email_data:
                        emails.append(email_data)
                    
                    if (i + 1) % 50 == 0:
                        logger.info(f"Processed {i + 1}/{len(message_ids)} emails")
                        
                except Exception as e:
                    logger.warning(f"Failed to process email {msg_id}: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(emails)} emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error loading emails: {e}")
            raise
    
    def _build_search_query(
        self,
        days_back: int,
        include_sent: bool,
        include_drafts: bool,
        custom_query: Optional[str]
    ) -> str:
        """Build Gmail search query.
        
        Args:
            days_back: Number of days back to search
            include_sent: Whether to include sent emails
            include_drafts: Whether to include draft emails
            custom_query: Custom query to append
            
        Returns:
            Gmail search query string
        """
        query_parts = []
        
        # Date filter
        if days_back:
            date_filter = datetime.now() - timedelta(days=days_back)
            query_parts.append(f"after:{date_filter.strftime('%Y/%m/%d')}")
        
        # Include/exclude sent emails
        if not include_sent:
            query_parts.append("-in:sent")
        
        # Include/exclude drafts
        if not include_drafts:
            query_parts.append("-in:drafts")
        
        # Exclude spam and trash
        query_parts.extend(["-in:spam", "-in:trash"])
        
        # Add custom query
        if custom_query:
            query_parts.append(custom_query)
        
        return " ".join(query_parts)
    
    def _get_message_ids(self, query: str, max_results: int) -> List[str]:
        """Get list of message IDs matching the query.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results
            
        Returns:
            List of message IDs
        """
        message_ids = []
        next_page_token = None
        
        while len(message_ids) < max_results:
            try:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(500, max_results - len(message_ids)),
                    pageToken=next_page_token
                ).execute()
                
                messages = results.get('messages', [])
                message_ids.extend([msg['id'] for msg in messages])
                
                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except Exception as e:
                logger.error(f"Error getting message IDs: {e}")
                break
        
        return message_ids[:max_results]
    
    def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific email.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Email data dictionary or None if failed
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
            
            # Extract body
            body = self._extract_email_body(message['payload'])
            
            # Parse date
            date_str = headers.get('Date', '')
            try:
                date_obj = email.utils.parsedate_to_datetime(date_str)
            except:
                date_obj = datetime.now()
            
            return {
                'id': message_id,
                'thread_id': message.get('threadId'),
                'subject': headers.get('Subject', ''),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'cc': headers.get('Cc', ''),
                'bcc': headers.get('Bcc', ''),
                'date': date_obj.isoformat(),
                'body': body,
                'labels': message.get('labelIds', []),
                'snippet': message.get('snippet', ''),
                'source': 'gmail',
                'source_id': message_id,
                'url': f"https://mail.google.com/mail/u/0/#inbox/{message_id}"
            }
            
        except Exception as e:
            logger.error(f"Error getting email details for {message_id}: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload.
        
        Args:
            payload: Email payload from Gmail API
            
        Returns:
            Email body text
        """
        body = ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                body += self._extract_email_body(part)
        else:
            # Single part message
            if payload.get('mimeType') == 'text/plain':
                data = payload.get('body', {}).get('data', '')
                if data:
                    try:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                    except Exception as e:
                        logger.warning(f"Failed to decode email body: {e}")
            elif payload.get('mimeType') == 'text/html':
                # For HTML, we might want to extract text content
                data = payload.get('body', {}).get('data', '')
                if data:
                    try:
                        html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Simple HTML to text conversion (could be improved)
                        import re
                        body = re.sub('<[^<]+?>', '', html_content)
                    except Exception as e:
                        logger.warning(f"Failed to decode HTML email body: {e}")
        
        return body.strip()
    
    def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search emails with a specific query.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results
            
        Returns:
            List of matching emails
        """
        return self.load_emails(
            max_emails=max_results,
            query=query
        )