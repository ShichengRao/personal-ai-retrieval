# Personal AI Retrieval System - Implementation Plan

## Overview
Building a personal AI assistant that indexes local Mac files and Google Suite data, enabling natural language queries and actions.

## Implementation Tickets

### Phase 1: Foundation & Setup
- **T001**: Set up Python project structure with requirements.txt
- **T002**: Configure environment variables and config.yaml template
- **T003**: Set up ChromaDB for vector storage
- **T004**: Implement basic embedding service (OpenAI + fallback to sentence-transformers)
- **T005**: Create basic CLI framework

### Phase 2: Data Ingestion Layer
- **T006**: Implement local file document loaders (PDF, TXT, DOCX, Markdown)
- **T007**: Set up Google API authentication (OAuth2)
- **T008**: Implement Gmail API integration for email ingestion
- **T009**: Implement Google Calendar API integration
- **T010**: Implement Google Drive API integration (Docs/Sheets)
- **T011**: Create unified ingestion pipeline with metadata tracking

### Phase 3: Indexing & Storage
- **T012**: Implement text chunking strategy for large documents
- **T013**: Create embedding generation and storage pipeline
- **T014**: Implement metadata storage alongside embeddings
- **T015**: Add incremental indexing (avoid re-processing unchanged files)
- **T016**: Create database schema and migration system

### Phase 4: Query & Retrieval
- **T017**: Implement semantic search using vector similarity
- **T018**: Create query preprocessing and intent detection
- **T019**: Implement retrieval-augmented generation (RAG) pipeline
- **T020**: Add source attribution and confidence scoring
- **T021**: Implement query result ranking and filtering

### Phase 5: AI Integration & Actions
- **T022**: Set up LLM integration (OpenAI GPT-4 + local model fallback)
- **T023**: Implement tool calling framework for actions
- **T024**: Create Gmail search and analysis tools
- **T025**: Create Calendar event creation and management tools
- **T026**: Implement meeting extraction from emails
- **T027**: Add natural language to structured data conversion

### Phase 6: CLI Interface
- **T028**: Create main assistant CLI with argument parsing
- **T029**: Implement ingestion CLI commands
- **T030**: Add query interface with conversation history
- **T031**: Implement action confirmation and feedback
- **T032**: Add verbose/debug modes for troubleshooting

### Phase 7: Testing & Validation
- **T033**: Create unit tests for core components
- **T034**: Add integration tests for Google APIs
- **T035**: Test end-to-end workflows (ingestion → query → action)
- **T036**: Performance testing with large document sets
- **T037**: Security audit for credential handling

### Phase 8: Documentation & Polish
- **T038**: Create comprehensive README with setup instructions
- **T039**: Add API documentation and code comments
- **T040**: Create example queries and use cases
- **T041**: Add error handling and user-friendly messages
- **T042**: Implement logging and monitoring

## Technical Architecture

### Core Components
1. **Document Loaders** (`src/loaders/`)
   - LocalFileLoader
   - GmailLoader
   - CalendarLoader
   - DriveLoader

2. **Embedding Service** (`src/embeddings/`)
   - OpenAIEmbeddings
   - LocalEmbeddings (sentence-transformers)

3. **Vector Database** (`src/storage/`)
   - ChromaDBManager
   - MetadataStore

4. **Query Engine** (`src/query/`)
   - SemanticSearch
   - RAGPipeline
   - ResultRanker

5. **Action Tools** (`src/tools/`)
   - GmailTools
   - CalendarTools
   - FileTools

6. **CLI Interface** (`src/cli/`)
   - AssistantCLI
   - IngestionCLI

### Data Flow
1. **Ingestion**: Documents → Text Extraction → Chunking → Embeddings → ChromaDB
2. **Query**: User Input → Intent Detection → Vector Search → LLM Processing → Response
3. **Actions**: Query Analysis → Tool Selection → API Calls → Confirmation

### Security Considerations
- Local storage of all embeddings and cache
- OAuth2 for Google APIs with minimal scopes
- Environment variables for API keys
- No data transmission except to chosen LLM provider

## MVP Deliverables
1. CLI tool for ingesting local files and Google data
2. Natural language query interface
3. Email-to-calendar event creation
4. Source attribution for all responses
5. Configuration management

## Success Metrics
- Successfully index 1000+ documents
- Sub-2 second query response time
- 90%+ accuracy for meeting extraction
- Zero credential exposure