"""Google API authentication utilities."""

import os
import pickle
from pathlib import Path
from typing import Optional, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GoogleAuthManager:
    """Manager for Google API authentication."""
    
    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ):
        """Initialize Google authentication manager.
        
        Args:
            credentials_file: Path to Google credentials JSON file
            token_file: Path to store/load token file
            scopes: List of OAuth scopes to request
        """
        self.credentials_file = credentials_file or config.google_credentials_file
        self.token_file = token_file or config.google_token_file
        self.scopes = scopes or config.google_scopes
        
        if not self.credentials_file:
            raise ValueError("Google credentials file path is required")
        
        if not Path(self.credentials_file).exists():
            raise FileNotFoundError(f"Google credentials file not found: {self.credentials_file}")
        
        self._credentials = None
    
    def get_credentials(self) -> Credentials:
        """Get valid Google API credentials.
        
        Returns:
            Valid Google credentials
        """
        if self._credentials and self._credentials.valid:
            return self._credentials
        
        # Load existing token if available
        if self.token_file and Path(self.token_file).exists():
            try:
                with open(self.token_file, 'rb') as token:
                    self._credentials = pickle.load(token)
                logger.info("Loaded existing Google credentials")
            except Exception as e:
                logger.warning(f"Failed to load existing token: {e}")
                self._credentials = None
        
        # Refresh credentials if they exist but are expired
        if self._credentials and not self._credentials.valid:
            if self._credentials.expired and self._credentials.refresh_token:
                try:
                    self._credentials.refresh(Request())
                    logger.info("Refreshed Google credentials")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    self._credentials = None
        
        # If we still don't have valid credentials, run OAuth flow
        if not self._credentials or not self._credentials.valid:
            self._credentials = self._run_oauth_flow()
        
        # Save credentials for next time
        if self.token_file and self._credentials:
            try:
                # Create directory if it doesn't exist
                Path(self.token_file).parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self._credentials, token)
                logger.info(f"Saved Google credentials to {self.token_file}")
            except Exception as e:
                logger.warning(f"Failed to save credentials: {e}")
        
        return self._credentials
    
    def _run_oauth_flow(self) -> Credentials:
        """Run OAuth flow to get new credentials.
        
        Returns:
            New Google credentials
        """
        logger.info("Starting Google OAuth flow")
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file,
                self.scopes
            )
            
            # Run local server flow
            credentials = flow.run_local_server(port=0)
            logger.info("Successfully completed Google OAuth flow")
            
            return credentials
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {e}")
            raise
    
    def revoke_credentials(self) -> None:
        """Revoke and delete stored credentials."""
        if self._credentials:
            try:
                self._credentials.revoke(Request())
                logger.info("Revoked Google credentials")
            except Exception as e:
                logger.warning(f"Failed to revoke credentials: {e}")
        
        # Delete token file
        if self.token_file and Path(self.token_file).exists():
            try:
                Path(self.token_file).unlink()
                logger.info("Deleted stored credentials")
            except Exception as e:
                logger.warning(f"Failed to delete token file: {e}")
        
        self._credentials = None
    
    def is_authenticated(self) -> bool:
        """Check if we have valid credentials.
        
        Returns:
            True if authenticated, False otherwise
        """
        try:
            creds = self.get_credentials()
            return creds and creds.valid
        except Exception:
            return False