# API Reference

This document provides detailed information about the Personal AI Retrieval System's APIs and components.

## Core Components

### Configuration Management

#### `personal_ai.utils.config.Config`

Manages application configuration from YAML files and environment variables.

```python
from personal_ai.utils.config import config

# Get configuration values
api_key = config.get('openai.api_key')
chunk_size = config.get('text_processing.chunk_size', 1000)

# Set configuration values
config.set('custom.setting', 'value')

# Save configuration
config.save()
```

**Properties:**
- `openai_api_key`: OpenAI API key
- `openai_model`: OpenAI model name
- `vector_db_path`: Vector database path
- `google_credentials_file`: Google credentials file path

### Embedding Services

#### `personal_ai.embeddings.base.EmbeddingService`

Abstract base class for embedding services.

```python
from personal_ai.embeddings.factory import get_default_embedding_service

embedding_service = get_default_embedding_service()

# Generate single embedding
embedding = embedding_service.embed_text("Hello world")

# Generate multiple embeddings
embeddings = embedding_service.embed_texts(["Text 1", "Text 2"])

# Get model info
dimension = embedding_service.dimension
model_name = embedding_service.model_name
```

#### `personal_ai.embeddings.openai_embeddings.OpenAIEmbeddings`

OpenAI-based embedding service.

```python
from personal_ai.embeddings.openai_embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    api_key="your-key",
    model="text-embedding-3-large"
)
```

#### `personal_ai.embeddings.local_embeddings.LocalEmbeddings`

Local embedding service using sentence-transformers.

```python
from personal_ai.embeddings.local_embeddings import LocalEmbeddings

embeddings = LocalEmbeddings(
    model_name="all-MiniLM-L6-v2",
    device="cpu"
)
```

### Vector Database

#### `personal_ai.storage.chroma_manager.ChromaManager`

ChromaDB vector database manager.

```python
from personal_ai.storage.chroma_manager import ChromaManager

db = ChromaManager(
    persist_directory="./data/chroma_db",
    collection_name="documents"
)

# Add documents
ids = db.add_documents(
    texts=["Document 1", "Document 2"],
    embeddings=[[0.1, 0.2], [0.3, 0.4]],
    metadatas=[{"source": "file1"}, {"source": "file2"}]
)

# Query documents
results = db.query(
    query_embeddings=[[0.1, 0.2]],
    n_results=5
)

# Get document count
count = db.count()
```

### Text Processing

#### `personal_ai.utils.text_processing.TextChunker`

Splits text into manageable chunks for processing.

```python
from personal_ai.utils.text_processing import TextChunker

chunker = TextChunker(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = chunker.chunk_text(
    text="Long document text...",
    metadata={"source": "document.pdf"}
)

# Each chunk has 'text' and 'metadata' fields
for chunk in chunks:
    print(f"Text: {chunk['text'][:100]}...")
    print(f"Metadata: {chunk['metadata']}")
```

#### `personal_ai.utils.text_processing.TextPreprocessor`

Text preprocessing utilities.

```python
from personal_ai.utils.text_processing import TextPreprocessor

# Extract keywords
keywords = TextPreprocessor.extract_keywords(
    "Machine learning and artificial intelligence",
    max_keywords=5
)

# Extract entities
entities = TextPreprocessor.extract_entities(
    "Contact john@example.com or visit https://example.com"
)

# Create summary
summary = TextPreprocessor.summarize_text(
    "Long text to summarize...",
    max_sentences=3
)
```

### Data Loaders

#### `personal_ai.loaders.local_file_loader.LocalFileLoader`

Loads and processes local files.

```python
from personal_ai.loaders.local_file_loader import LocalFileLoader

loader = LocalFileLoader()

documents = loader.load_files(
    paths=["~/Documents"],
    file_types=[".pdf", ".txt"],
    exclude_patterns=["*.tmp"],
    recursive=True
)

# Check if file changed
changed = loader.is_file_changed("/path/to/file.pdf", "old_hash")
```

#### `personal_ai.loaders.gmail_loader.GmailLoader`

Loads emails from Gmail.

```python
from personal_ai.loaders.gmail_loader import GmailLoader
from personal_ai.loaders.google_auth import GoogleAuthManager

auth = GoogleAuthManager()
loader = GmailLoader(auth)

emails = loader.load_emails(
    max_emails=100,
    days_back=7,
    include_sent=True
)

# Search emails
results = loader.search_emails("project meeting", max_results=10)
```

#### `personal_ai.loaders.calendar_loader.CalendarLoader`

Loads events from Google Calendar.

```python
from personal_ai.loaders.calendar_loader import CalendarLoader

loader = CalendarLoader(auth)

events = loader.load_events(
    days_back=30,
    days_forward=90,
    include_declined=False
)

# Create new event
event = loader.create_event(
    summary="Team Meeting",
    start_time=datetime(2024, 1, 15, 14, 0),
    end_time=datetime(2024, 1, 15, 15, 0),
    description="Weekly team sync",
    attendees=["colleague@example.com"]
)
```

### Search and Query

#### `personal_ai.query.semantic_search.SemanticSearch`

Semantic search engine for querying documents.

```python
from personal_ai.query.semantic_search import SemanticSearch

search = SemanticSearch()

results = search.search(
    query="machine learning project",
    max_results=10,
    similarity_threshold=0.7,
    filters={"source": "local_file"}
)

# Find similar documents
similar = search.find_similar_documents(
    document_id="doc123",
    max_results=5
)
```

#### `personal_ai.query.rag_pipeline.RAGPipeline`

Retrieval-Augmented Generation pipeline.

```python
from personal_ai.query.rag_pipeline import RAGPipeline

rag = RAGPipeline()

response = rag.answer_query(
    query="What's my next meeting?",
    max_context_length=4000,
    max_results=5,
    conversation_history=[
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ]
)

# Analyze query intent
intent = rag.analyze_query_intent("Add meeting tomorrow at 2pm")
```

### Tools System

#### `personal_ai.tools.base.BaseTool`

Base class for creating AI tools.

```python
from personal_ai.tools.base import BaseTool

class CustomTool(BaseTool):
    @property
    def name(self):
        return "custom_tool"
    
    @property
    def description(self):
        return "A custom tool for specific tasks"
    
    @property
    def parameters(self):
        return {
            "param1": {
                "type": "string",
                "description": "First parameter"
            }
        }
    
    def execute(self, **kwargs):
        return {"result": "Custom tool executed"}
```

#### `personal_ai.tools.base.ToolRegistry`

Registry for managing tools.

```python
from personal_ai.tools.base import tool_registry

# Register a tool
tool_registry.register(CustomTool())

# Execute a tool
result = tool_registry.execute_tool("custom_tool", param1="value")

# Get available tools
tools = tool_registry.list_tools()
```

### Built-in Tools

#### Gmail Tools

```python
from personal_ai.tools.gmail_tools import SearchGmailTool, GetRecentEmailsTool

# Search emails
search_tool = SearchGmailTool()
result = search_tool.execute(
    query="project meeting",
    max_results=10,
    days_back=7
)

# Get recent emails
recent_tool = GetRecentEmailsTool()
result = recent_tool.execute(
    max_emails=10,
    days_back=1,
    include_sent=False
)
```

#### Calendar Tools

```python
from personal_ai.tools.calendar_tools import GetUpcomingEventsTool, CreateCalendarEventTool

# Get upcoming events
upcoming_tool = GetUpcomingEventsTool()
result = upcoming_tool.execute(days_forward=7)

# Create calendar event
create_tool = CreateCalendarEventTool()
result = create_tool.execute(
    summary="Team Meeting",
    start_datetime="2024-01-15T14:00:00",
    end_datetime="2024-01-15T15:00:00",
    description="Weekly sync",
    attendees=["colleague@example.com"]
)
```

#### Search Tools

```python
from personal_ai.tools.search_tools import SearchDocumentsTool

search_tool = SearchDocumentsTool()
result = search_tool.execute(
    query="machine learning",
    max_results=5,
    source_filter="local_file",
    similarity_threshold=0.7
)
```

## CLI Commands

### Ingestion CLI (`pai-ingest`)

```bash
# Index all sources
pai-ingest all

# Index specific sources
pai-ingest local --paths ~/Documents --file-types .pdf .txt
pai-ingest gmail --max-emails 500 --days-back 14
pai-ingest calendar --days-back 30 --days-forward 60
pai-ingest drive --max-files 100

# Check status
pai-ingest status
```

### Assistant CLI (`pai-assistant`)

```bash
# Interactive mode
pai-assistant ask

# Direct queries
pai-assistant ask "What's my next meeting?"

# Search documents
pai-assistant search "machine learning" --source local_file

# Quick commands
pai-assistant upcoming --days 7
pai-assistant recent-emails --days 1
pai-assistant status
```

## Configuration Schema

### Main Configuration (`config.yaml`)

```yaml
# OpenAI Configuration
openai:
  api_key: string
  model: string (default: "gpt-4")
  embedding_model: string (default: "text-embedding-3-large")

# Local Embeddings
local_embeddings:
  model_name: string (default: "all-MiniLM-L6-v2")
  device: string (default: "cpu")

# Vector Database
vector_db:
  persist_directory: string (default: "./data/chroma_db")
  collection_name: string (default: "personal_docs")

# Google API
google:
  credentials_file: string
  token_file: string
  scopes: list[string]

# Local Files
local_files:
  paths: list[string]
  file_types: list[string]
  exclude_patterns: list[string]

# Gmail
gmail:
  max_emails: integer (default: 1000)
  days_back: integer (default: 30)
  include_sent: boolean (default: true)
  include_drafts: boolean (default: false)

# Calendar
calendar:
  days_back: integer (default: 30)
  days_forward: integer (default: 90)
  include_declined: boolean (default: false)

# Text Processing
text_processing:
  chunk_size: integer (default: 1000)
  chunk_overlap: integer (default: 200)
  max_tokens_per_chunk: integer (default: 8000)

# Query
query:
  max_results: integer (default: 10)
  similarity_threshold: float (default: 0.7)
  include_metadata: boolean (default: true)

# Logging
logging:
  level: string (default: "INFO")
  file: string (default: "./logs/assistant.log")
```

### Environment Variables (`.env`)

```bash
# OpenAI
OPENAI_API_KEY=string

# Google
GOOGLE_CREDENTIALS_FILE=string
GOOGLE_TOKEN_FILE=string

# Database
CHROMA_DB_PATH=string

# Logging
LOG_LEVEL=string
LOG_FILE=string
```

## Error Handling

### Common Exceptions

```python
# Configuration errors
from personal_ai.utils.config import Config
try:
    config = Config("nonexistent.yaml")
except FileNotFoundError:
    print("Config file not found")

# Authentication errors
from personal_ai.loaders.google_auth import GoogleAuthManager
try:
    auth = GoogleAuthManager()
    creds = auth.get_credentials()
except ValueError as e:
    print(f"Authentication error: {e}")

# Embedding errors
from personal_ai.embeddings.openai_embeddings import OpenAIEmbeddings
try:
    embeddings = OpenAIEmbeddings()
    result = embeddings.embed_text("test")
except Exception as e:
    print(f"Embedding error: {e}")
```

### Logging

```python
from personal_ai.utils.logging import get_logger

logger = get_logger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

## Extension Points

### Custom Embedding Service

```python
from personal_ai.embeddings.base import EmbeddingService

class CustomEmbeddingService(EmbeddingService):
    def embed_text(self, text: str) -> List[float]:
        # Custom implementation
        pass
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Custom implementation
        pass
    
    @property
    def dimension(self) -> int:
        return 768  # Your model's dimension
    
    @property
    def model_name(self) -> str:
        return "custom-model"
```

### Custom Data Loader

```python
from typing import List, Dict, Any

class CustomLoader:
    def load_documents(self) -> List[Dict[str, Any]]:
        # Return list of documents with required fields:
        # - id, content, source, source_id, url
        # - Plus any custom metadata
        pass
```

### Custom Tool

```python
from personal_ai.tools.base import BaseTool, tool_registry

class CustomActionTool(BaseTool):
    @property
    def name(self):
        return "custom_action"
    
    @property
    def description(self):
        return "Performs a custom action"
    
    @property
    def parameters(self):
        return {
            "action_type": {
                "type": "string",
                "description": "Type of action to perform"
            }
        }
    
    def execute(self, action_type: str) -> Dict[str, Any]:
        # Implement your custom action
        return {"success": True, "action": action_type}

# Register the tool
tool_registry.register(CustomActionTool())
```

This API reference provides the foundation for extending and customizing the Personal AI Retrieval System to meet your specific needs.