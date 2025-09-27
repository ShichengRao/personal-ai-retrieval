# Personal AI Retrieval System

A powerful personal AI assistant that indexes your local files and Google Suite data, enabling natural language queries and automated actions. Built with Python, ChromaDB, and OpenAI/local LLMs.

## 🚀 Features

- **Multi-Source Indexing**: Index local files (PDF, DOCX, TXT, Markdown) and Google Suite data (Gmail, Calendar, Drive)
- **Semantic Search**: Find relevant information using natural language queries
- **AI-Powered Responses**: Get intelligent answers with source attribution
- **Action Capabilities**: Create calendar events, analyze emails for meetings, and more
- **CLI Interface**: Easy-to-use command-line tools for ingestion and querying
- **Flexible Configuration**: Support for both OpenAI and local embedding models

## 📋 Requirements

- Python 3.11+
- Google API credentials (for Gmail/Calendar/Drive integration)
- OpenAI API key (optional, for advanced AI features)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/personal-ai-retrieval.git
   cd personal-ai-retrieval
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package**:
   ```bash
   pip install -e .
   ```

## ⚙️ Configuration

1. **Copy configuration template**:
   ```bash
   cp config.yaml.template config.yaml
   cp .env.template .env
   ```

2. **Set up Google API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API, Calendar API, and Drive API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the JSON file and save as `credentials/google_credentials.json`

3. **Configure OpenAI (optional)**:
   ```bash
   # Add to .env file
   OPENAI_API_KEY=your-openai-api-key-here
   ```

4. **Edit configuration**:
   ```yaml
   # config.yaml
   local_files:
     paths:
       - "~/Documents"
       - "~/Desktop"
     file_types:
       - ".pdf"
       - ".txt"
       - ".docx"
       - ".md"
   
   gmail:
     max_emails: 1000
     days_back: 30
   
   calendar:
     days_back: 30
     days_forward: 90
   ```

## 🔄 Data Ingestion

Index your data sources using the ingestion CLI:

### Index All Sources
```bash
pai-ingest all
```

### Index Specific Sources
```bash
# Local files only
pai-ingest local --paths ~/Documents --file-types .pdf .txt

# Gmail only
pai-ingest gmail --max-emails 500 --days-back 14

# Calendar only
pai-ingest calendar --days-back 30 --days-forward 60

# Google Drive only
pai-ingest drive --max-files 100
```

### Check Status
```bash
pai-ingest status
```

## 💬 Using the Assistant

### Interactive Mode
```bash
pai-assistant ask
```

### Direct Queries
```bash
pai-assistant ask "What's my next meeting?"
pai-assistant ask "Summarize today's emails"
pai-assistant ask "Find documents about project planning"
```

### Search Documents
```bash
pai-assistant search "machine learning" --source local_file
```

### Quick Commands
```bash
# Show upcoming events
pai-assistant upcoming --days 7

# Show recent emails
pai-assistant recent-emails --days 1

# Check system status
pai-assistant status
```

## 📖 Example Queries

The assistant can handle various types of natural language queries:

### Calendar & Scheduling
- "What's my next meeting?"
- "Do I have any meetings with John next week?"
- "When is the strategy session?"
- "Add a meeting with Sarah tomorrow at 2pm"

### Email Analysis
- "Summarize today's emails"
- "Find emails about the project deadline"
- "Check my email for any meeting invitations"
- "Who sent me emails about the budget?"

### Document Search
- "Find documents about machine learning"
- "Show me PDFs from last month"
- "Search for files containing 'quarterly report'"

### Cross-Source Queries
- "Find the email about next week's strategy session and show me the calendar event"
- "What documents are related to the project mentioned in yesterday's meeting?"

## 🔧 Advanced Configuration

### Embedding Models

**OpenAI Embeddings** (Recommended):
```yaml
openai:
  api_key: "your-key"
  embedding_model: "text-embedding-3-large"
```

**Local Embeddings** (Fallback):
```yaml
local_embeddings:
  model_name: "all-MiniLM-L6-v2"
  device: "cpu"  # or "cuda"
```

### Text Processing
```yaml
text_processing:
  chunk_size: 1000
  chunk_overlap: 200
  max_tokens_per_chunk: 8000
```

### Vector Database
```yaml
vector_db:
  persist_directory: "./data/chroma_db"
  collection_name: "personal_docs"
```

## 🛡️ Security & Privacy

- **Local Storage**: All embeddings and data are stored locally
- **OAuth2**: Secure authentication with Google APIs
- **No Data Transmission**: Only embeddings/queries sent to LLM providers (if using OpenAI)
- **Credential Management**: Secure handling of API keys and tokens

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing    │    │     Storage     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Local Files   │───▶│ • Text Chunking │───▶│ • ChromaDB      │
│ • Gmail         │    │ • Embeddings    │    │ • Metadata      │
│ • Calendar      │    │ • Preprocessing │    │ • Vector Index  │
│ • Google Drive  │    └─────────────────┘    └─────────────────┘
└─────────────────┘                                    │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   AI Pipeline   │◀───│   Retrieval     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Natural Lang. │    │ • Semantic      │    │ • Vector Search │
│ • CLI Interface │    │   Search        │    │ • Ranking       │
│ • Actions       │    │ • RAG Pipeline  │    │ • Filtering     │
└─────────────────┘    │ • Tool Calling  │    └─────────────────┘
                       └─────────────────┘
```

## 🔌 Available Tools

The assistant includes several built-in tools:

### Gmail Tools
- `search_gmail`: Search emails with queries
- `get_recent_emails`: Get recent emails
- `analyze_email_for_meetings`: Extract meeting info from emails

### Calendar Tools
- `get_upcoming_events`: Get upcoming calendar events
- `search_calendar_events`: Search calendar events
- `create_calendar_event`: Create new calendar events
- `parse_meeting_from_text`: Parse meeting info from text

### Search Tools
- `search_documents`: Search indexed documents
- `find_similar_documents`: Find similar documents
- `search_by_source`: Search by data source

## 🚨 Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**Google API Authentication**:
```bash
# Check credentials file exists
ls credentials/google_credentials.json

# Re-run OAuth flow
rm credentials/google_token.json
pai-ingest gmail  # Will trigger re-authentication
```

**ChromaDB Issues**:
```bash
# Clear and rebuild database
rm -rf data/chroma_db
pai-ingest all --force
```

**Memory Issues**:
```yaml
# Reduce chunk size in config.yaml
text_processing:
  chunk_size: 500
  max_tokens_per_chunk: 4000
```

### Logs

Check logs for detailed error information:
```bash
tail -f logs/assistant.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ChromaDB](https://www.trychroma.com/) for vector database
- [OpenAI](https://openai.com/) for embeddings and LLM APIs
- [LangChain](https://langchain.com/) for AI pipeline components
- [Google APIs](https://developers.google.com/) for data integration

## 📞 Support

- Create an issue for bug reports or feature requests
- Check the [documentation](docs/) for detailed guides
- Review the [FAQ](docs/FAQ.md) for common questions

---

**Built with ❤️ for personal productivity and AI-powered knowledge management.**