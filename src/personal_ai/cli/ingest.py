"""CLI for data ingestion."""

import click
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm

from ..loaders.local_file_loader import LocalFileLoader
from ..loaders.gmail_loader import GmailLoader
from ..loaders.calendar_loader import CalendarLoader
from ..loaders.drive_loader import DriveLoader
from ..loaders.google_auth import GoogleAuthManager
from ..embeddings.factory import get_default_embedding_service
from ..storage.chroma_manager import ChromaManager
from ..utils.text_processing import TextChunker
from ..utils.config import config
from ..utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.option('--config-file', '-c', help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(config_file: Optional[str], verbose: bool):
    """Personal AI Assistant - Data Ingestion CLI"""
    # Setup logging
    log_level = 'DEBUG' if verbose else 'INFO'
    setup_logging(level=log_level)
    
    # Load config if specified
    if config_file:
        config.config_path = Path(config_file)
        config._config = config._load_config()
    
    logger.info("Personal AI Assistant - Data Ingestion CLI")


@cli.command()
@click.option('--paths', '-p', multiple=True, help='Paths to index (can be specified multiple times)')
@click.option('--file-types', '-t', multiple=True, help='File types to include (e.g., .pdf, .txt)')
@click.option('--exclude', '-e', multiple=True, help='Patterns to exclude')
@click.option('--recursive/--no-recursive', default=True, help='Scan directories recursively')
@click.option('--force', '-f', is_flag=True, help='Force re-indexing of all files')
def local(paths: List[str], file_types: List[str], exclude: List[str], recursive: bool, force: bool):
    """Index local files."""
    logger.info("Starting local file indexing")
    
    try:
        # Initialize components
        loader = LocalFileLoader()
        embedding_service = get_default_embedding_service()
        vector_db = ChromaManager()
        chunker = TextChunker()
        
        # Use provided paths or config defaults
        scan_paths = list(paths) if paths else config.get('local_files.paths', ['~/Documents'])
        scan_file_types = list(file_types) if file_types else config.get('local_files.file_types', ['.pdf', '.txt', '.md', '.docx'])
        exclude_patterns = list(exclude) if exclude else config.get('local_files.exclude_patterns', [])
        
        logger.info(f"Scanning paths: {scan_paths}")
        logger.info(f"File types: {scan_file_types}")
        
        # Load files
        documents = loader.load_files(
            paths=scan_paths,
            file_types=scan_file_types,
            exclude_patterns=exclude_patterns,
            recursive=recursive
        )
        
        if not documents:
            logger.warning("No documents found to index")
            return
        
        logger.info(f"Found {len(documents)} documents to process")
        
        # Process documents
        indexed_count = 0
        skipped_count = 0
        
        with tqdm(total=len(documents), desc="Processing files") as pbar:
            for doc in documents:
                try:
                    doc_id = doc['source_id']
                    
                    # Check if document needs updating (unless force is specified)
                    if not force and vector_db.document_exists(doc_id):
                        # Check if file has changed
                        stored_hash = _get_stored_file_hash(vector_db, doc_id)
                        if stored_hash == doc.get('file_hash'):
                            skipped_count += 1
                            pbar.update(1)
                            continue
                        else:
                            # File changed, delete old version
                            vector_db.delete_documents(ids=[doc_id])
                    
                    # Chunk the document
                    chunks = chunker.chunk_text(doc['content'], metadata=doc)
                    
                    if not chunks:
                        logger.warning(f"No chunks generated for {doc['name']}")
                        pbar.update(1)
                        continue
                    
                    # Generate embeddings
                    texts = [chunk['text'] for chunk in chunks]
                    embeddings = embedding_service.embed_texts(texts)
                    
                    # Prepare metadata for each chunk
                    metadatas = []
                    chunk_ids = []
                    
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{doc_id}_chunk_{i}"
                        chunk_ids.append(chunk_id)
                        
                        metadata = chunk['metadata'].copy()
                        metadata.update({
                            'chunk_id': chunk_id,
                            'parent_doc_id': doc_id
                        })
                        metadatas.append(metadata)
                    
                    # Store in vector database
                    vector_db.add_documents(
                        texts=texts,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        ids=chunk_ids
                    )
                    
                    indexed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {doc.get('name', 'unknown')}: {e}")
                
                pbar.update(1)
        
        logger.info(f"Indexing complete: {indexed_count} files indexed, {skipped_count} files skipped")
        
    except Exception as e:
        logger.error(f"Error during local file indexing: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--max-emails', '-m', type=int, help='Maximum number of emails to index')
@click.option('--days-back', '-d', type=int, help='Number of days back to index')
@click.option('--include-sent/--no-sent', default=True, help='Include sent emails')
@click.option('--force', '-f', is_flag=True, help='Force re-indexing of all emails')
def gmail(max_emails: Optional[int], days_back: Optional[int], include_sent: bool, force: bool):
    """Index Gmail emails."""
    logger.info("Starting Gmail indexing")
    
    try:
        # Initialize components
        auth_manager = GoogleAuthManager()
        loader = GmailLoader(auth_manager)
        embedding_service = get_default_embedding_service()
        vector_db = ChromaManager()
        chunker = TextChunker()
        
        # Use provided values or config defaults
        max_emails = max_emails or config.get('gmail.max_emails', 1000)
        days_back = days_back or config.get('gmail.days_back', 30)
        
        logger.info(f"Loading up to {max_emails} emails from last {days_back} days")
        
        # Load emails
        emails = loader.load_emails(
            max_emails=max_emails,
            days_back=days_back,
            include_sent=include_sent
        )
        
        if not emails:
            logger.warning("No emails found to index")
            return
        
        logger.info(f"Found {len(emails)} emails to process")
        
        # Process emails
        indexed_count = 0
        skipped_count = 0
        
        with tqdm(total=len(emails), desc="Processing emails") as pbar:
            for email in emails:
                try:
                    email_id = email['source_id']
                    
                    # Check if email already indexed (unless force is specified)
                    if not force and vector_db.document_exists(email_id):
                        skipped_count += 1
                        pbar.update(1)
                        continue
                    
                    # Prepare content for chunking
                    content_parts = [
                        f"Subject: {email.get('subject', '')}",
                        f"From: {email.get('from', '')}",
                        f"To: {email.get('to', '')}",
                        email.get('body', '')
                    ]
                    content = '\n'.join([part for part in content_parts if part.strip()])
                    
                    # Chunk the email
                    chunks = chunker.chunk_text(content, metadata=email)
                    
                    if not chunks:
                        logger.warning(f"No chunks generated for email {email.get('subject', 'No Subject')}")
                        pbar.update(1)
                        continue
                    
                    # Generate embeddings
                    texts = [chunk['text'] for chunk in chunks]
                    embeddings = embedding_service.embed_texts(texts)
                    
                    # Prepare metadata for each chunk
                    metadatas = []
                    chunk_ids = []
                    
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{email_id}_chunk_{i}"
                        chunk_ids.append(chunk_id)
                        
                        metadata = chunk['metadata'].copy()
                        metadata.update({
                            'chunk_id': chunk_id,
                            'parent_doc_id': email_id
                        })
                        metadatas.append(metadata)
                    
                    # Store in vector database
                    vector_db.add_documents(
                        texts=texts,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        ids=chunk_ids
                    )
                    
                    indexed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing email {email.get('subject', 'unknown')}: {e}")
                
                pbar.update(1)
        
        logger.info(f"Gmail indexing complete: {indexed_count} emails indexed, {skipped_count} emails skipped")
        
    except Exception as e:
        logger.error(f"Error during Gmail indexing: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--days-back', '-b', type=int, help='Number of days back to index')
@click.option('--days-forward', '-f', type=int, help='Number of days forward to index')
@click.option('--include-declined/--no-declined', default=False, help='Include declined events')
@click.option('--force', is_flag=True, help='Force re-indexing of all events')
def calendar(days_back: Optional[int], days_forward: Optional[int], include_declined: bool, force: bool):
    """Index Google Calendar events."""
    logger.info("Starting Calendar indexing")
    
    try:
        # Initialize components
        auth_manager = GoogleAuthManager()
        loader = CalendarLoader(auth_manager)
        embedding_service = get_default_embedding_service()
        vector_db = ChromaManager()
        chunker = TextChunker()
        
        # Use provided values or config defaults
        days_back = days_back or config.get('calendar.days_back', 30)
        days_forward = days_forward or config.get('calendar.days_forward', 90)
        
        logger.info(f"Loading calendar events from {days_back} days back to {days_forward} days forward")
        
        # Load events
        events = loader.load_events(
            days_back=days_back,
            days_forward=days_forward,
            include_declined=include_declined
        )
        
        if not events:
            logger.warning("No calendar events found to index")
            return
        
        logger.info(f"Found {len(events)} events to process")
        
        # Process events
        indexed_count = 0
        skipped_count = 0
        
        with tqdm(total=len(events), desc="Processing events") as pbar:
            for event in events:
                try:
                    event_id = event['source_id']
                    
                    # Check if event already indexed (unless force is specified)
                    if not force and vector_db.document_exists(event_id):
                        skipped_count += 1
                        pbar.update(1)
                        continue
                    
                    # Use the full_text field for indexing
                    content = event.get('full_text', '')
                    
                    if not content.strip():
                        logger.warning(f"No content for event {event.get('summary', 'No Title')}")
                        pbar.update(1)
                        continue
                    
                    # Chunk the event (usually events are short, so might be just one chunk)
                    chunks = chunker.chunk_text(content, metadata=event)
                    
                    if not chunks:
                        pbar.update(1)
                        continue
                    
                    # Generate embeddings
                    texts = [chunk['text'] for chunk in chunks]
                    embeddings = embedding_service.embed_texts(texts)
                    
                    # Prepare metadata for each chunk
                    metadatas = []
                    chunk_ids = []
                    
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{event_id}_chunk_{i}"
                        chunk_ids.append(chunk_id)
                        
                        metadata = chunk['metadata'].copy()
                        metadata.update({
                            'chunk_id': chunk_id,
                            'parent_doc_id': event_id
                        })
                        metadatas.append(metadata)
                    
                    # Store in vector database
                    vector_db.add_documents(
                        texts=texts,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        ids=chunk_ids
                    )
                    
                    indexed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing event {event.get('summary', 'unknown')}: {e}")
                
                pbar.update(1)
        
        logger.info(f"Calendar indexing complete: {indexed_count} events indexed, {skipped_count} events skipped")
        
    except Exception as e:
        logger.error(f"Error during Calendar indexing: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--max-files', '-m', type=int, help='Maximum number of files to index')
@click.option('--include-shared/--no-shared', default=True, help='Include shared files')
@click.option('--force', '-f', is_flag=True, help='Force re-indexing of all files')
def drive(max_files: Optional[int], include_shared: bool, force: bool):
    """Index Google Drive documents."""
    logger.info("Starting Google Drive indexing")
    
    try:
        # Initialize components
        auth_manager = GoogleAuthManager()
        loader = DriveLoader(auth_manager)
        embedding_service = get_default_embedding_service()
        vector_db = ChromaManager()
        chunker = TextChunker()
        
        max_files = max_files or 1000
        
        logger.info(f"Loading up to {max_files} Drive documents")
        
        # Load documents
        documents = loader.load_documents(
            max_files=max_files,
            include_shared=include_shared
        )
        
        if not documents:
            logger.warning("No Drive documents found to index")
            return
        
        logger.info(f"Found {len(documents)} documents to process")
        
        # Process documents
        indexed_count = 0
        skipped_count = 0
        
        with tqdm(total=len(documents), desc="Processing Drive docs") as pbar:
            for doc in documents:
                try:
                    doc_id = doc['source_id']
                    
                    # Check if document already indexed (unless force is specified)
                    if not force and vector_db.document_exists(doc_id):
                        skipped_count += 1
                        pbar.update(1)
                        continue
                    
                    content = doc.get('content', '')
                    
                    if not content.strip():
                        logger.warning(f"No content for document {doc.get('name', 'Untitled')}")
                        pbar.update(1)
                        continue
                    
                    # Chunk the document
                    chunks = chunker.chunk_text(content, metadata=doc)
                    
                    if not chunks:
                        pbar.update(1)
                        continue
                    
                    # Generate embeddings
                    texts = [chunk['text'] for chunk in chunks]
                    embeddings = embedding_service.embed_texts(texts)
                    
                    # Prepare metadata for each chunk
                    metadatas = []
                    chunk_ids = []
                    
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{doc_id}_chunk_{i}"
                        chunk_ids.append(chunk_id)
                        
                        metadata = chunk['metadata'].copy()
                        metadata.update({
                            'chunk_id': chunk_id,
                            'parent_doc_id': doc_id
                        })
                        metadatas.append(metadata)
                    
                    # Store in vector database
                    vector_db.add_documents(
                        texts=texts,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        ids=chunk_ids
                    )
                    
                    indexed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc.get('name', 'unknown')}: {e}")
                
                pbar.update(1)
        
        logger.info(f"Drive indexing complete: {indexed_count} documents indexed, {skipped_count} documents skipped")
        
    except Exception as e:
        logger.error(f"Error during Drive indexing: {e}")
        raise click.ClickException(str(e))


@cli.command()
@click.option('--local/--no-local', default=True, help='Index local files')
@click.option('--gmail/--no-gmail', default=True, help='Index Gmail')
@click.option('--calendar/--no-calendar', default=True, help='Index Calendar')
@click.option('--drive/--no-drive', default=False, help='Index Google Drive')
@click.option('--force', '-f', is_flag=True, help='Force re-indexing of all data')
def all(local: bool, gmail: bool, calendar: bool, drive: bool, force: bool):
    """Index all configured data sources."""
    logger.info("Starting full data indexing")
    
    try:
        if local:
            logger.info("=== Indexing Local Files ===")
            ctx = click.Context(cli.commands['local'])
            ctx.invoke(cli.commands['local'], force=force)
        
        if gmail:
            logger.info("=== Indexing Gmail ===")
            ctx = click.Context(cli.commands['gmail'])
            ctx.invoke(cli.commands['gmail'], force=force)
        
        if calendar:
            logger.info("=== Indexing Calendar ===")
            ctx = click.Context(cli.commands['calendar'])
            ctx.invoke(cli.commands['calendar'], force=force)
        
        if drive:
            logger.info("=== Indexing Google Drive ===")
            ctx = click.Context(cli.commands['drive'])
            ctx.invoke(cli.commands['drive'], force=force)
        
        logger.info("Full indexing complete!")
        
    except Exception as e:
        logger.error(f"Error during full indexing: {e}")
        raise click.ClickException(str(e))


@cli.command()
def status():
    """Show indexing status and statistics."""
    try:
        vector_db = ChromaManager()
        
        total_docs = vector_db.count()
        
        click.echo(f"Total indexed chunks: {total_docs}")
        
        # Get counts by source
        sources = ['local_file', 'gmail', 'google_calendar', 'google_drive']
        
        for source in sources:
            try:
                results = vector_db.get_documents(
                    where={'source': source},
                    limit=1,
                    include=[]
                )
                count = len(results.get('ids', []))
                if count > 0:
                    # This is just a sample, actual count would require scanning all docs
                    click.echo(f"  {source}: {count}+ chunks")
            except:
                click.echo(f"  {source}: 0 chunks")
        
        # Show embedding service info
        try:
            embedding_service = get_default_embedding_service()
            click.echo(f"Embedding model: {embedding_service.model_name}")
            click.echo(f"Embedding dimension: {embedding_service.dimension}")
        except Exception as e:
            click.echo(f"Embedding service error: {e}")
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise click.ClickException(str(e))


def _get_stored_file_hash(vector_db: ChromaManager, doc_id: str) -> Optional[str]:
    """Get stored file hash for a document."""
    try:
        results = vector_db.get_documents(
            ids=[doc_id],
            include=['metadatas']
        )
        
        if results.get('metadatas') and results['metadatas'][0]:
            return results['metadatas'][0].get('file_hash')
    except:
        pass
    
    return None


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()