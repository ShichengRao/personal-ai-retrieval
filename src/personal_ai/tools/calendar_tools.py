"""Calendar-related tools for AI actions."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

from .base import BaseTool
from ..loaders.calendar_loader import CalendarLoader
from ..loaders.google_auth import GoogleAuthManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GetUpcomingEventsTool(BaseTool):
    """Tool for getting upcoming calendar events."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize upcoming events tool.
        
        Args:
            auth_manager: Google authentication manager
        """
        self.calendar_loader = CalendarLoader(auth_manager)
    
    @property
    def name(self) -> str:
        return "get_upcoming_events"
    
    @property
    def description(self) -> str:
        return "Get upcoming calendar events. Useful for answering questions about schedule and meetings."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "days_forward": {
                "type": "integer",
                "description": "Number of days forward to look for events (default: 7)",
                "default": 7
            },
            "max_events": {
                "type": "integer",
                "description": "Maximum number of events to return (default: 20)",
                "default": 20
            }
        }
    
    def execute(self, days_forward: int = 7, max_events: int = 20) -> Dict[str, Any]:
        """Get upcoming calendar events.
        
        Args:
            days_forward: Days forward to search
            max_events: Maximum events to return
            
        Returns:
            Upcoming events
        """
        try:
            events = self.calendar_loader.load_events(
                days_back=0,  # Only future events
                days_forward=days_forward
            )
            
            # Filter to only future events and sort by start time
            now = datetime.now()
            future_events = []
            
            for event in events:
                start_time_str = event.get('start_time', '')
                if start_time_str:
                    try:
                        # Parse the start time
                        if 'T' in start_time_str:  # DateTime format
                            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        else:  # Date format (all-day event)
                            start_time = datetime.fromisoformat(start_time_str + 'T00:00:00')
                        
                        if start_time > now:
                            future_events.append((start_time, event))
                    except:
                        continue
            
            # Sort by start time and limit results
            future_events.sort(key=lambda x: x[0])
            upcoming_events = [event for _, event in future_events[:max_events]]
            
            # Format for LLM consumption
            formatted_events = []
            for event in upcoming_events:
                formatted_events.append({
                    'summary': event.get('summary', ''),
                    'start_time': event.get('start_time', ''),
                    'end_time': event.get('end_time', ''),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'attendees': [
                        {
                            'name': attendee.get('name', ''),
                            'email': attendee.get('email', ''),
                            'response': attendee.get('response', '')
                        }
                        for attendee in event.get('attendees', [])
                    ],
                    'all_day': event.get('all_day', False),
                    'url': event.get('url', '')
                })
            
            return {
                'events': formatted_events,
                'count': len(formatted_events),
                'period': f"Next {days_forward} days"
            }
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return {
                'error': str(e),
                'events': [],
                'count': 0
            }


class SearchCalendarEventsTool(BaseTool):
    """Tool for searching calendar events."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize calendar search tool.
        
        Args:
            auth_manager: Google authentication manager
        """
        self.calendar_loader = CalendarLoader(auth_manager)
    
    @property
    def name(self) -> str:
        return "search_calendar_events"
    
    @property
    def description(self) -> str:
        return "Search calendar events by keyword or phrase. Useful for finding specific meetings or events."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Search query for calendar events (e.g., 'strategy meeting', 'John', 'standup')"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of events to return (default: 10)",
                "default": 10
            }
        }
    
    def execute(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search calendar events.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            Search results
        """
        try:
            events = self.calendar_loader.search_events(query, max_results)
            
            # Format for LLM consumption
            formatted_events = []
            for event in events:
                formatted_events.append({
                    'summary': event.get('summary', ''),
                    'start_time': event.get('start_time', ''),
                    'end_time': event.get('end_time', ''),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'attendees': [
                        {
                            'name': attendee.get('name', ''),
                            'email': attendee.get('email', ''),
                            'response': attendee.get('response', '')
                        }
                        for attendee in event.get('attendees', [])
                    ],
                    'all_day': event.get('all_day', False),
                    'url': event.get('url', '')
                })
            
            return {
                'events': formatted_events,
                'count': len(formatted_events),
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error searching calendar events: {e}")
            return {
                'error': str(e),
                'events': [],
                'count': 0
            }


class CreateCalendarEventTool(BaseTool):
    """Tool for creating calendar events."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize calendar creation tool.
        
        Args:
            auth_manager: Google authentication manager
        """
        self.calendar_loader = CalendarLoader(auth_manager)
    
    @property
    def name(self) -> str:
        return "create_calendar_event"
    
    @property
    def description(self) -> str:
        return "Create a new calendar event. Use this when the user asks to schedule a meeting or add something to their calendar."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "summary": {
                "type": "string",
                "description": "Event title/summary"
            },
            "start_datetime": {
                "type": "string",
                "description": "Start date and time in ISO format (e.g., '2024-01-15T14:00:00')"
            },
            "end_datetime": {
                "type": "string",
                "description": "End date and time in ISO format (e.g., '2024-01-15T15:00:00')"
            },
            "description": {
                "type": "string",
                "description": "Event description (optional)",
                "default": ""
            },
            "location": {
                "type": "string",
                "description": "Event location (optional)",
                "default": ""
            },
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of attendee email addresses (optional)",
                "default": []
            }
        }
    
    def execute(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: str = "",
        location: str = "",
        attendees: List[str] = None
    ) -> Dict[str, Any]:
        """Create a calendar event.
        
        Args:
            summary: Event title
            start_datetime: Start datetime in ISO format
            end_datetime: End datetime in ISO format
            description: Event description
            location: Event location
            attendees: List of attendee emails
            
        Returns:
            Creation result
        """
        try:
            # Parse datetime strings
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = datetime.fromisoformat(end_datetime)
            
            # Create the event
            event = self.calendar_loader.create_event(
                summary=summary,
                start_time=start_dt,
                end_time=end_dt,
                description=description,
                location=location,
                attendees=attendees or []
            )
            
            return {
                'success': True,
                'event': {
                    'summary': event.get('summary', ''),
                    'start_time': event.get('start_time', ''),
                    'end_time': event.get('end_time', ''),
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'url': event.get('url', '')
                },
                'message': f"Successfully created event: {summary}"
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to create event: {str(e)}"
            }


class ParseMeetingFromTextTool(BaseTool):
    """Tool for parsing meeting information from text."""
    
    @property
    def name(self) -> str:
        return "parse_meeting_from_text"
    
    @property
    def description(self) -> str:
        return "Parse meeting information (date, time, participants, topic) from natural language text."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "text": {
                "type": "string",
                "description": "Text containing meeting information to parse"
            }
        }
    
    def execute(self, text: str) -> Dict[str, Any]:
        """Parse meeting information from text.
        
        Args:
            text: Text to parse
            
        Returns:
            Parsed meeting information
        """
        try:
            meeting_info = {
                'dates': [],
                'times': [],
                'participants': [],
                'topics': [],
                'locations': [],
                'meeting_links': []
            }
            
            # Extract dates
            date_patterns = [
                r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                r'\b\d{4}-\d{2}-\d{2}\b',
                r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b',
                r'\b(?:today|tomorrow|next\s+week|this\s+week)\b'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                meeting_info['dates'].extend(matches)
            
            # Extract times
            time_patterns = [
                r'\b\d{1,2}:\d{2}\s*(?:am|pm)\b',
                r'\b\d{1,2}\s*(?:am|pm)\b',
                r'\b(?:morning|afternoon|evening|noon)\b'
            ]
            
            for pattern in time_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                meeting_info['times'].extend(matches)
            
            # Extract email addresses (potential participants)
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            meeting_info['participants'] = re.findall(email_pattern, text)
            
            # Extract meeting links
            link_patterns = [
                r'https://[^\s]*zoom[^\s]*',
                r'https://[^\s]*teams[^\s]*',
                r'https://[^\s]*meet[^\s]*',
                r'https://[^\s]*webex[^\s]*'
            ]
            
            for pattern in link_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                meeting_info['meeting_links'].extend(matches)
            
            # Extract potential topics (simple keyword extraction)
            topic_keywords = [
                'meeting', 'discussion', 'review', 'standup', 'sync', 'planning',
                'strategy', 'project', 'demo', 'presentation', 'interview',
                'call', 'conference', 'workshop', 'training'
            ]
            
            for keyword in topic_keywords:
                if keyword in text.lower():
                    # Try to extract context around the keyword
                    pattern = rf'\b\w*{keyword}\w*\b'
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    meeting_info['topics'].extend(matches)
            
            # Remove duplicates
            for key in meeting_info:
                meeting_info[key] = list(set(meeting_info[key]))
            
            # Try to suggest a meeting title
            suggested_title = self._suggest_meeting_title(text, meeting_info)
            
            return {
                'parsed_info': meeting_info,
                'suggested_title': suggested_title,
                'confidence': self._calculate_parsing_confidence(meeting_info)
            }
            
        except Exception as e:
            logger.error(f"Error parsing meeting from text: {e}")
            return {
                'error': str(e),
                'parsed_info': {},
                'confidence': 0.0
            }
    
    def _suggest_meeting_title(self, text: str, meeting_info: Dict[str, Any]) -> str:
        """Suggest a meeting title based on parsed information.
        
        Args:
            text: Original text
            meeting_info: Parsed meeting information
            
        Returns:
            Suggested meeting title
        """
        # Look for common meeting title patterns
        title_patterns = [
            r'(?:meeting|call|discussion|sync)\s+(?:about|on|for|regarding)\s+([^.!?]+)',
            r'([^.!?]+)\s+(?:meeting|call|discussion|sync)',
            r'(?:let\'s|we should|need to)\s+(?:discuss|talk about|meet about)\s+([^.!?]+)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 100:
                    return title.title()
        
        # Fallback: use topics if available
        if meeting_info.get('topics'):
            return f"Meeting: {', '.join(meeting_info['topics'][:2])}"
        
        return "Meeting"
    
    def _calculate_parsing_confidence(self, meeting_info: Dict[str, Any]) -> float:
        """Calculate confidence score for parsing results.
        
        Args:
            meeting_info: Parsed meeting information
            
        Returns:
            Confidence score between 0 and 1
        """
        score = 0.0
        
        # Award points for different types of information found
        if meeting_info.get('dates'):
            score += 0.3
        if meeting_info.get('times'):
            score += 0.3
        if meeting_info.get('participants'):
            score += 0.2
        if meeting_info.get('topics'):
            score += 0.1
        if meeting_info.get('meeting_links'):
            score += 0.1
        
        return min(score, 1.0)