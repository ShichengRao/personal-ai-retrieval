# Setup Guide

This guide will walk you through setting up the Personal AI Retrieval System from scratch.

## Prerequisites

- Python 3.11 or higher
- Git
- Google account (for Gmail/Calendar/Drive integration)
- OpenAI account (optional, for advanced AI features)

## Step 1: Installation

### 1.1 Clone the Repository
```bash
git clone https://github.com/your-username/personal-ai-retrieval.git
cd personal-ai-retrieval
```

### 1.2 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

### 1.4 Verify Installation
```bash
python3 test_core.py
```

You should see all tests passing.

## Step 2: Google API Setup

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" or select existing project
3. Give your project a name (e.g., "Personal AI Assistant")
4. Click "Create"

### 2.2 Enable APIs

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for and enable the following APIs:
   - Gmail API
   - Google Calendar API
   - Google Drive API

### 2.3 Create Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (app name, user support email, developer email)
   - Add your email to test users
4. For OAuth client ID:
   - Application type: "Desktop application"
   - Name: "Personal AI Assistant"
5. Download the JSON file

### 2.4 Save Credentials

```bash
mkdir -p credentials
# Copy the downloaded JSON file to credentials/google_credentials.json
cp ~/Downloads/client_secret_*.json credentials/google_credentials.json
```

## Step 3: Configuration

### 3.1 Copy Configuration Templates
```bash
cp config.yaml.template config.yaml
cp .env.template .env
```

### 3.2 Configure Environment Variables

Edit `.env` file:
```bash
# OpenAI API Key (optional)
OPENAI_API_KEY=your-openai-api-key-here

# Google API Credentials
GOOGLE_CREDENTIALS_FILE=./credentials/google_credentials.json
GOOGLE_TOKEN_FILE=./credentials/google_token.json

# Database Configuration
CHROMA_DB_PATH=./data/chroma_db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/assistant.log
```

### 3.3 Configure Application Settings

Edit `config.yaml`:

```yaml
# OpenAI Configuration (optional)
openai:
  api_key: "your-openai-api-key-here"  # Or use environment variable
  model: "gpt-4"
  embedding_model: "text-embedding-3-large"

# Local Embedding Model (fallback)
local_embeddings:
  model_name: "all-MiniLM-L6-v2"
  device: "cpu"

# Vector Database
vector_db:
  persist_directory: "./data/chroma_db"
  collection_name: "personal_docs"

# Google API Configuration
google:
  credentials_file: "./credentials/google_credentials.json"
  token_file: "./credentials/google_token.json"
  scopes:
    - "https://www.googleapis.com/auth/gmail.readonly"
    - "https://www.googleapis.com/auth/calendar"
    - "https://www.googleapis.com/auth/drive.readonly"

# Local File Indexing
local_files:
  paths:
    - "~/Documents"
    - "~/Desktop"
    - "~/Downloads"  # Add more paths as needed
  file_types:
    - ".pdf"
    - ".txt"
    - ".docx"
    - ".md"
    - ".py"
  exclude_patterns:
    - "*.tmp"
    - "*.log"
    - ".git/*"
    - "node_modules/*"
    - "__pycache__/*"

# Gmail Configuration
gmail:
  max_emails: 1000
  days_back: 30
  include_sent: true
  include_drafts: false

# Calendar Configuration
calendar:
  days_back: 30
  days_forward: 90
  include_declined: false

# Text Processing
text_processing:
  chunk_size: 1000
  chunk_overlap: 200
  max_tokens_per_chunk: 8000

# Query Configuration
query:
  max_results: 10
  similarity_threshold: 0.7
  include_metadata: true

# Logging
logging:
  level: "INFO"
  file: "./logs/assistant.log"
```

## Step 4: First Run and Authentication

### 4.1 Create Required Directories
```bash
mkdir -p data logs credentials
```

### 4.2 Test Google Authentication

Run a small ingestion to trigger OAuth flow:
```bash
pai-ingest gmail --max-emails 5
```

This will:
1. Open your browser for Google OAuth
2. Ask you to sign in and grant permissions
3. Save authentication tokens for future use

### 4.3 Verify Setup
```bash
pai-assistant status
```

You should see all components as "✅ Connected" or "✅ Available".

## Step 5: Initial Data Ingestion

### 5.1 Start with Local Files
```bash
pai-ingest local --paths ~/Documents --file-types .pdf .txt .md
```

### 5.2 Index Gmail (Start Small)
```bash
pai-ingest gmail --max-emails 100 --days-back 7
```

### 5.3 Index Calendar
```bash
pai-ingest calendar --days-back 30 --days-forward 30
```

### 5.4 Check Indexing Status
```bash
pai-ingest status
```

## Step 6: Test the Assistant

### 6.1 Interactive Mode
```bash
pai-assistant ask
```

Try some queries:
- "What's my next meeting?"
- "Find documents about project"
- "Summarize recent emails"

### 6.2 Direct Queries
```bash
pai-assistant ask "What meetings do I have this week?"
pai-assistant search "machine learning" --source local_file
pai-assistant upcoming --days 7
```

## Troubleshooting

### Google Authentication Issues

**Error: "Access blocked"**
- Make sure your app is in testing mode
- Add your email to test users in OAuth consent screen

**Error: "Credentials not found"**
```bash
# Check file exists and has correct permissions
ls -la credentials/google_credentials.json
# Re-download from Google Cloud Console if needed
```

**Error: "Token expired"**
```bash
# Delete token file to force re-authentication
rm credentials/google_token.json
pai-ingest gmail --max-emails 1
```

### Embedding Issues

**Error: "OpenAI API key not found"**
- Either add OpenAI API key to `.env` file
- Or let the system fall back to local embeddings (slower but free)

**Error: "Model download failed"**
```bash
# For local embeddings, ensure internet connection for first download
# Models are cached locally after first download
```

### Memory Issues

**Error: "Out of memory"**
- Reduce chunk size in config.yaml
- Process fewer files at once
- Use local embeddings instead of OpenAI

### Permission Issues

**Error: "Permission denied"**
```bash
# Make sure directories are writable
chmod 755 data logs credentials
```

## Performance Optimization

### For Large Document Collections

1. **Batch Processing**:
   ```bash
   # Process files in smaller batches
   pai-ingest local --paths ~/Documents/folder1
   pai-ingest local --paths ~/Documents/folder2
   ```

2. **Selective Indexing**:
   ```yaml
   # In config.yaml, be selective about file types
   local_files:
     file_types:
       - ".pdf"  # Only PDFs for now
   ```

3. **Incremental Updates**:
   ```bash
   # Regular incremental updates (only new/changed files)
   pai-ingest all  # Without --force flag
   ```

### For Better Query Performance

1. **Adjust Similarity Threshold**:
   ```yaml
   query:
     similarity_threshold: 0.8  # Higher = more precise, fewer results
   ```

2. **Optimize Chunk Size**:
   ```yaml
   text_processing:
     chunk_size: 500  # Smaller chunks = more precise matching
   ```

## Next Steps

1. **Set up Automation**: Create cron jobs for regular data ingestion
2. **Customize Tools**: Add your own tools for specific workflows
3. **Integrate with Other Services**: Extend to support more data sources
4. **Fine-tune Configuration**: Adjust settings based on your usage patterns

## Getting Help

- Check the [FAQ](FAQ.md) for common questions
- Review logs in `logs/assistant.log` for detailed error information
- Create an issue on GitHub for bugs or feature requests