"""Configuration management for the Personal AI Assistant."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager that loads from YAML and environment variables."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config.yaml file. Defaults to ./config.yaml
        """
        # Load environment variables
        load_dotenv()
        
        # Set default config path
        if config_path is None:
            config_path = Path.cwd() / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable overrides."""
        config = {}
        
        # Load from YAML file if it exists
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        return config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to config."""
        # OpenAI configuration
        if os.getenv('OPENAI_API_KEY'):
            config.setdefault('openai', {})['api_key'] = os.getenv('OPENAI_API_KEY')
        
        # Claude configuration
        if os.getenv('CLAUDE_API_KEY'):
            config.setdefault('claude', {})['api_key'] = os.getenv('CLAUDE_API_KEY')
        
        # Google credentials
        if os.getenv('GOOGLE_CREDENTIALS_FILE'):
            config.setdefault('google', {})['credentials_file'] = os.getenv('GOOGLE_CREDENTIALS_FILE')
        
        if os.getenv('GOOGLE_TOKEN_FILE'):
            config.setdefault('google', {})['token_file'] = os.getenv('GOOGLE_TOKEN_FILE')
        
        # Database path
        if os.getenv('CHROMA_DB_PATH'):
            config.setdefault('vector_db', {})['persist_directory'] = os.getenv('CHROMA_DB_PATH')
        
        # Logging
        if os.getenv('LOG_LEVEL'):
            config.setdefault('logging', {})['level'] = os.getenv('LOG_LEVEL')
        
        if os.getenv('LOG_FILE'):
            config.setdefault('logging', {})['file'] = os.getenv('LOG_FILE')
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'openai.api_key')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save current configuration to YAML file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        return self.get('openai.api_key')
    
    @property
    def openai_model(self) -> str:
        """Get OpenAI model name."""
        return self.get('openai.model', 'gpt-4')
    
    @property
    def openai_embedding_model(self) -> str:
        """Get OpenAI embedding model name."""
        return self.get('openai.embedding_model', 'text-embedding-3-large')
    
    @property
    def local_embedding_model(self) -> str:
        """Get local embedding model name."""
        return self.get('local_embeddings.model_name', 'all-MiniLM-L6-v2')
    
    @property
    def vector_db_path(self) -> str:
        """Get vector database persist directory."""
        return self.get('vector_db.persist_directory', './data/chroma_db')
    
    @property
    def vector_db_collection(self) -> str:
        """Get vector database collection name."""
        return self.get('vector_db.collection_name', 'personal_docs')
    
    @property
    def google_credentials_file(self) -> Optional[str]:
        """Get Google credentials file path."""
        return self.get('google.credentials_file')
    
    @property
    def google_token_file(self) -> Optional[str]:
        """Get Google token file path."""
        return self.get('google.token_file')
    
    @property
    def google_scopes(self) -> list:
        """Get Google API scopes."""
        return self.get('google.scopes', [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/drive.readonly'
        ])
    
    @property
    def claude_api_key(self) -> Optional[str]:
        """Get Claude API key."""
        return self.get('claude.api_key')
    
    @property
    def claude_model(self) -> str:
        """Get Claude model name."""
        return self.get('claude.model', 'claude-sonnet-4-5')
    
    @property
    def claude_max_tokens(self) -> int:
        """Get Claude max tokens."""
        return self.get('claude.max_tokens', 4000)
    
    @property
    def prefer_claude(self) -> bool:
        """Check if Claude is preferred over OpenAI."""
        return self.get('llm.prefer_claude', False)
    
    @property
    def prefer_openai(self) -> bool:
        """Check if OpenAI is preferred over Claude."""
        return self.get('llm.prefer_openai', True)


# Global config instance
config = Config()