"""Google Calendar API loader for calendar events."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build

from .google_auth import GoogleAuthManager
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CalendarLoader:
    """Loader for Google Calendar events using Google API."""
    
    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """Initialize Calendar loader.
        
        Args:
            auth_manager: Google authentication manager. If None, creates new one
        """
        self.auth_manager = auth_manager or GoogleAuthManager()
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize Calendar API service."""
        try:
            credentials = self.auth_manager.get_credentials()
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info("Initialized Calendar API service")
        except Exception as e:
            logger.error(f"Failed to initialize Calendar service: {e}")
            raise
    
    def load_events(
        self,
        days_back: Optional[int] = None,
        days_forward: Optional[int] = None,
        include_declined: bool = False,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """Load calendar events.
        
        Args:
            days_back: Number of days back to search
            days_forward: Number of days forward to search
            include_declined: Whether to include declined events
            calendar_id: Calendar ID to search (default: primary)
            
        Returns:
            List of event dictionaries with metadata
        """
        days_back = days_back or config.get('calendar.days_back', 30)
        days_forward = days_forward or config.get('calendar.days_forward', 90)
        include_declined = include_declined if include_declined is not None else config.get('calendar.include_declined', False)
        
        # Calculate time range
        time_min = (datetime.now() - timedelta(days=days_back)).isoformat() + 'Z'
        time_max = (datetime.now() + timedelta(days=days_forward)).isoformat() + 'Z'
        
        logger.info(f"Loading calendar events from {time_min} to {time_max}")
        
        try:
            events = []
            page_token = None
            
            while True:
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=2500,  # Maximum allowed by API
                    singleEvents=True,
                    orderBy='startTime',
                    pageToken=page_token
                ).execute()
                
                page_events = events_result.get('items', [])
                
                for event in page_events:
                    # Skip declined events if not included
                    if not include_declined:
                        attendees = event.get('attendees', [])
                        user_response = None
                        for attendee in attendees:
                            if attendee.get('self'):
                                user_response = attendee.get('responseStatus')
                                break
                        
                        if user_response == 'declined':
                            continue
                    
                    event_data = self._process_event(event, calendar_id)
                    if event_data:
                        events.append(event_data)
                
                page_token = events_result.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Successfully loaded {len(events)} calendar events")
            return events
            
        except Exception as e:
            logger.error(f"Error loading calendar events: {e}")
            raise
    
    def _process_event(self, event: Dict[str, Any], calendar_id: str) -> Optional[Dict[str, Any]]:
        """Process a single calendar event.
        
        Args:
            event: Raw event data from Calendar API
            calendar_id: Calendar ID
            
        Returns:
            Processed event data or None if failed
        """
        try:
            # Extract start and end times
            start = event.get('start', {})
            end = event.get('end', {})
            
            start_time = start.get('dateTime') or start.get('date')
            end_time = end.get('dateTime') or end.get('date')
            
            # Parse attendees
            attendees = []
            for attendee in event.get('attendees', []):
                attendees.append({
                    'email': attendee.get('email'),
                    'name': attendee.get('displayName'),
                    'response': attendee.get('responseStatus'),
                    'organizer': attendee.get('organizer', False)
                })
            
            # Extract location and description
            location = event.get('location', '')
            description = event.get('description', '')
            
            # Build full text content for indexing
            full_text_parts = [
                event.get('summary', ''),
                description,
                location,
                f"Attendees: {', '.join([a.get('name') or a.get('email', '') for a in attendees if a.get('name') or a.get('email')])}"
            ]
            full_text = '\n'.join([part for part in full_text_parts if part.strip()])
            
            return {
                'id': event['id'],
                'calendar_id': calendar_id,
                'summary': event.get('summary', ''),
                'description': description,
                'location': location,
                'start_time': start_time,
                'end_time': end_time,
                'all_day': 'date' in start,  # All-day events use 'date' instead of 'dateTime'
                'attendees': attendees,
                'organizer': event.get('organizer', {}),
                'status': event.get('status'),
                'created': event.get('created'),
                'updated': event.get('updated'),
                'recurring_event_id': event.get('recurringEventId'),
                'html_link': event.get('htmlLink'),
                'full_text': full_text,
                'source': 'google_calendar',
                'source_id': event['id'],
                'url': event.get('htmlLink', '')
            }
            
        except Exception as e:
            logger.error(f"Error processing calendar event {event.get('id')}: {e}")
            return None
    
    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """Create a new calendar event.
        
        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Event description
            location: Event location
            attendees: List of attendee email addresses
            calendar_id: Calendar ID to create event in
            
        Returns:
            Created event data
        """
        try:
            event_body = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                }
            }
            
            if description:
                event_body['description'] = description
            
            if location:
                event_body['location'] = location
            
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()
            
            logger.info(f"Created calendar event: {event.get('htmlLink')}")
            return self._process_event(event, calendar_id)
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            raise
    
    def search_events(
        self,
        query: str,
        max_results: int = 10,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """Search calendar events.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            calendar_id: Calendar ID to search
            
        Returns:
            List of matching events
        """
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                q=query,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                event_data = self._process_event(event, calendar_id)
                if event_data:
                    events.append(event_data)
            
            logger.info(f"Found {len(events)} events matching query: {query}")
            return events
            
        except Exception as e:
            logger.error(f"Error searching calendar events: {e}")
            raise
    
    def get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of available calendars.
        
        Returns:
            List of calendar information
        """
        try:
            calendar_list = self.service.calendarList().list().execute()
            
            calendars = []
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar['id'],
                    'summary': calendar.get('summary'),
                    'description': calendar.get('description'),
                    'primary': calendar.get('primary', False),
                    'access_role': calendar.get('accessRole')
                })
            
            logger.info(f"Found {len(calendars)} calendars")
            return calendars
            
        except Exception as e:
            logger.error(f"Error getting calendars: {e}")
            raise