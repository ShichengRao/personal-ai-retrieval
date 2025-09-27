"""Gmail-related tools for AI actions."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base import BaseTool
from ..loaders.gmail_loader import GmailLoader
from ..loaders.google_auth import GoogleAuthManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SearchGmailTool(BaseTool):
    """Tool for searching Gmail emails."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize Gmail search tool.
        
        Args:
            auth_manager: Google authentication manager
        """
        self.gmail_loader = GmailLoader(auth_manager)
    
    @property
    def name(self) -> str:
        return "search_gmail"
    
    @property
    def description(self) -> str:
        return "Search Gmail emails with a query string. Returns recent emails matching the search criteria."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Gmail search query (e.g., 'from:john@example.com', 'subject:meeting', 'has:attachment')"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of emails to return (default: 10)",
                "default": 10
            },
            "days_back": {
                "type": "integer", 
                "description": "Number of days back to search (default: 7)",
                "default": 7
            }
        }
    
    def execute(self, query: str, max_results: int = 10, days_back: int = 7) -> Dict[str, Any]:
        """Execute Gmail search.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            days_back: Days back to search
            
        Returns:
            Search results
        """
        try:
            # Add date filter to query
            date_filter = datetime.now() - timedelta(days=days_back)
            full_query = f"{query} after:{date_filter.strftime('%Y/%m/%d')}"
            
            emails = self.gmail_loader.search_emails(full_query, max_results)
            
            # Format results for LLM consumption
            formatted_emails = []
            for email in emails:
                formatted_emails.append({
                    'subject': email.get('subject', ''),
                    'from': email.get('from', ''),
                    'to': email.get('to', ''),
                    'date': email.get('date', ''),
                    'snippet': email.get('snippet', ''),
                    'body_preview': email.get('body', '')[:500] + "..." if len(email.get('body', '')) > 500 else email.get('body', ''),
                    'url': email.get('url', '')
                })
            
            return {
                'emails': formatted_emails,
                'count': len(formatted_emails),
                'query': query,
                'search_period': f"Last {days_back} days"
            }
            
        except Exception as e:
            logger.error(f"Error searching Gmail: {e}")
            return {
                'error': str(e),
                'emails': [],
                'count': 0
            }


class AnalyzeEmailForMeetingsTool(BaseTool):
    """Tool for analyzing emails to extract meeting information."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize email analysis tool.
        
        Args:
            auth_manager: Google authentication manager
        """
        self.gmail_loader = GmailLoader(auth_manager)
    
    @property
    def name(self) -> str:
        return "analyze_email_for_meetings"
    
    @property
    def description(self) -> str:
        return "Analyze recent emails to extract meeting information like dates, times, participants, and topics."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "days_back": {
                "type": "integer",
                "description": "Number of days back to analyze emails (default: 3)",
                "default": 3
            },
            "max_emails": {
                "type": "integer",
                "description": "Maximum number of emails to analyze (default: 20)",
                "default": 20
            }
        }
    
    def execute(self, days_back: int = 3, max_emails: int = 20) -> Dict[str, Any]:
        """Analyze emails for meeting information.
        
        Args:
            days_back: Days back to analyze
            max_emails: Maximum emails to analyze
            
        Returns:
            Extracted meeting information
        """
        try:
            # Search for emails that might contain meeting information
            meeting_keywords = [
                "meeting", "call", "zoom", "teams", "conference", "appointment",
                "schedule", "calendar", "invite", "agenda", "discussion"
            ]
            
            query = " OR ".join(meeting_keywords)
            emails = self.gmail_loader.load_emails(
                max_emails=max_emails,
                days_back=days_back,
                query=query
            )
            
            meetings = []
            for email in emails:
                meeting_info = self._extract_meeting_info(email)
                if meeting_info:
                    meetings.append(meeting_info)
            
            return {
                'meetings_found': meetings,
                'count': len(meetings),
                'emails_analyzed': len(emails),
                'analysis_period': f"Last {days_back} days"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing emails for meetings: {e}")
            return {
                'error': str(e),
                'meetings_found': [],
                'count': 0
            }
    
    def _extract_meeting_info(self, email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract meeting information from an email.
        
        Args:
            email: Email data
            
        Returns:
            Meeting information or None
        """
        import re
        from datetime import datetime
        
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        content = f"{subject} {body}"
        
        # Check if this looks like a meeting-related email
        meeting_indicators = [
            'meeting', 'call', 'zoom', 'teams', 'conference', 'appointment',
            'schedule', 'calendar', 'invite', 'agenda', 'discussion'
        ]
        
        if not any(indicator in content for indicator in meeting_indicators):
            return None
        
        meeting_info = {
            'email_subject': email.get('subject', ''),
            'email_from': email.get('from', ''),
            'email_date': email.get('date', ''),
            'email_url': email.get('url', ''),
            'extracted_info': {}
        }
        
        # Extract potential dates and times
        date_patterns = [
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b'
        ]
        
        time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(?:am|pm)\b',
            r'\b\d{1,2}\s*(?:am|pm)\b'
        ]
        
        dates_found = []
        times_found = []
        
        for pattern in date_patterns:
            dates_found.extend(re.findall(pattern, content, re.IGNORECASE))
        
        for pattern in time_patterns:
            times_found.extend(re.findall(pattern, content, re.IGNORECASE))
        
        if dates_found:
            meeting_info['extracted_info']['dates'] = list(set(dates_found))
        
        if times_found:
            meeting_info['extracted_info']['times'] = list(set(times_found))
        
        # Extract potential participants (email addresses)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        participants = re.findall(email_pattern, body)
        if participants:
            meeting_info['extracted_info']['participants'] = list(set(participants))
        
        # Extract meeting links
        link_patterns = [
            r'https://[^\s]*zoom[^\s]*',
            r'https://[^\s]*teams[^\s]*',
            r'https://[^\s]*meet[^\s]*',
            r'https://[^\s]*webex[^\s]*'
        ]
        
        links = []
        for pattern in link_patterns:
            links.extend(re.findall(pattern, body, re.IGNORECASE))
        
        if links:
            meeting_info['extracted_info']['meeting_links'] = list(set(links))
        
        # Only return if we found some useful information
        if meeting_info['extracted_info']:
            return meeting_info
        
        return None


class GetRecentEmailsTool(BaseTool):
    """Tool for getting recent emails."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize recent emails tool.
        
        Args:
            auth_manager: Google authentication manager
        """
        self.gmail_loader = GmailLoader(auth_manager)
    
    @property
    def name(self) -> str:
        return "get_recent_emails"
    
    @property
    def description(self) -> str:
        return "Get recent emails from Gmail inbox. Useful for summarizing recent communications."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "max_emails": {
                "type": "integer",
                "description": "Maximum number of emails to retrieve (default: 10)",
                "default": 10
            },
            "days_back": {
                "type": "integer",
                "description": "Number of days back to retrieve emails (default: 1)",
                "default": 1
            },
            "include_sent": {
                "type": "boolean",
                "description": "Whether to include sent emails (default: false)",
                "default": False
            }
        }
    
    def execute(self, max_emails: int = 10, days_back: int = 1, include_sent: bool = False) -> Dict[str, Any]:
        """Get recent emails.
        
        Args:
            max_emails: Maximum emails to retrieve
            days_back: Days back to search
            include_sent: Include sent emails
            
        Returns:
            Recent emails
        """
        try:
            emails = self.gmail_loader.load_emails(
                max_emails=max_emails,
                days_back=days_back,
                include_sent=include_sent
            )
            
            # Format for LLM consumption
            formatted_emails = []
            for email in emails:
                formatted_emails.append({
                    'subject': email.get('subject', ''),
                    'from': email.get('from', ''),
                    'to': email.get('to', ''),
                    'date': email.get('date', ''),
                    'snippet': email.get('snippet', ''),
                    'labels': email.get('labels', []),
                    'url': email.get('url', '')
                })
            
            return {
                'emails': formatted_emails,
                'count': len(formatted_emails),
                'period': f"Last {days_back} day(s)",
                'includes_sent': include_sent
            }
            
        except Exception as e:
            logger.error(f"Error getting recent emails: {e}")
            return {
                'error': str(e),
                'emails': [],
                'count': 0
            }