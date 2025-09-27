"""CLI for the AI assistant."""

import click
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from ..query.rag_pipeline import RAGPipeline
from ..tools.base import tool_registry
from ..tools.gmail_tools import SearchGmailTool, AnalyzeEmailForMeetingsTool, GetRecentEmailsTool
from ..tools.calendar_tools import GetUpcomingEventsTool, SearchCalendarEventsTool, CreateCalendarEventTool, ParseMeetingFromTextTool
from ..tools.search_tools import SearchDocumentsTool, FindSimilarDocumentsTool, SearchBySourceTool
from ..loaders.google_auth import GoogleAuthManager
from ..utils.config import config
from ..utils.logging import setup_logging, get_logger

logger = get_logger(__name__)
console = Console()


@click.group()
@click.option('--config-file', '-c', help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config_file: Optional[str], verbose: bool):
    """Personal AI Assistant - Query Interface"""
    # Setup logging
    log_level = 'DEBUG' if verbose else 'INFO'
    setup_logging(level=log_level, console=False)  # Don't log to console in interactive mode
    
    # Load config if specified
    if config_file:
        config.config_path = Path(config_file)
        config._config = config._load_config()
    
    # Initialize tools
    _initialize_tools()
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


def _initialize_tools():
    """Initialize and register all available tools."""
    try:
        # Initialize Google auth manager (will be shared across tools)
        auth_manager = GoogleAuthManager()
        
        # Register Gmail tools
        tool_registry.register(SearchGmailTool(auth_manager))
        tool_registry.register(AnalyzeEmailForMeetingsTool(auth_manager))
        tool_registry.register(GetRecentEmailsTool(auth_manager))
        
        # Register Calendar tools
        tool_registry.register(GetUpcomingEventsTool(auth_manager))
        tool_registry.register(SearchCalendarEventsTool(auth_manager))
        tool_registry.register(CreateCalendarEventTool(auth_manager))
        tool_registry.register(ParseMeetingFromTextTool())
        
        # Register Search tools
        tool_registry.register(SearchDocumentsTool())
        tool_registry.register(FindSimilarDocumentsTool())
        tool_registry.register(SearchBySourceTool())
        
        logger.info(f"Initialized {len(tool_registry.list_tools())} tools")
        
    except Exception as e:
        logger.warning(f"Some tools may not be available: {e}")


@cli.command()
@click.argument('query', required=False)
@click.option('--max-results', '-n', type=int, default=5, help='Maximum number of results')
@click.option('--source', '-s', help='Filter by source (gmail, calendar, local_file, google_drive)')
@click.option('--json-output', '-j', is_flag=True, help='Output results as JSON')
@click.pass_context
def ask(ctx, query: Optional[str], max_results: int, source: Optional[str], json_output: bool):
    """Ask the AI assistant a question."""
    
    if not query:
        # Interactive mode
        _interactive_mode(ctx.obj.get('verbose', False))
        return
    
    try:
        # Initialize RAG pipeline
        rag = RAGPipeline()
        
        # Process the query
        with console.status("[bold green]Processing your query..."):
            result = rag.answer_query(
                query=query,
                max_results=max_results
            )
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            _display_answer(result)
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        if json_output:
            click.echo(json.dumps({'error': str(e)}))
        else:
            console.print(f"[red]Error: {e}[/red]")


def _interactive_mode(verbose: bool):
    """Run the assistant in interactive mode."""
    console.print(Panel.fit(
        "[bold blue]Personal AI Assistant[/bold blue]\n"
        "Ask me anything about your documents, emails, and calendar!\n"
        "Type 'help' for commands, 'quit' to exit.",
        title="Welcome"
    ))
    
    rag = RAGPipeline()
    conversation_history = []
    
    while True:
        try:
            # Get user input
            query = click.prompt('\n[You]', type=str, prompt_suffix=' ')
            
            if query.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if query.lower() == 'help':
                _show_help()
                continue
            
            if query.lower() == 'tools':
                _show_tools()
                continue
            
            if query.lower() == 'clear':
                conversation_history = []
                console.print("[green]Conversation history cleared.[/green]")
                continue
            
            # Process the query
            with console.status("[bold green]Thinking..."):
                result = rag.answer_query(
                    query=query,
                    conversation_history=conversation_history[-10:]  # Keep last 10 messages
                )
            
            # Display the answer
            _display_answer(result)
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": query})
            conversation_history.append({"role": "assistant", "content": result['answer']})
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            console.print(f"[red]Error: {e}[/red]")


def _display_answer(result: Dict[str, Any]):
    """Display the answer in a formatted way."""
    answer = result.get('answer', 'No answer provided')
    sources = result.get('sources', [])
    confidence = result.get('confidence', 0.0)
    
    # Display the answer
    console.print(Panel(
        Markdown(answer),
        title="[bold green]Assistant[/bold green]",
        border_style="green"
    ))
    
    # Display confidence if available
    if confidence > 0:
        confidence_color = "green" if confidence > 0.8 else "yellow" if confidence > 0.5 else "red"
        console.print(f"[{confidence_color}]Confidence: {confidence:.1%}[/{confidence_color}]")
    
    # Display sources if available
    if sources:
        console.print("\n[bold]Sources:[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Source", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Similarity", style="green")
        table.add_column("Date", style="yellow")
        
        for source in sources[:5]:  # Show top 5 sources
            similarity = f"{source.get('similarity', 0):.1%}" if source.get('similarity') else "N/A"
            date = source.get('date', '')[:10] if source.get('date') else ''  # Show just date part
            
            table.add_row(
                source.get('source', 'Unknown'),
                source.get('title', 'Untitled')[:50] + "..." if len(source.get('title', '')) > 50 else source.get('title', 'Untitled'),
                similarity,
                date
            )
        
        console.print(table)


def _show_help():
    """Show help information."""
    help_text = """
[bold]Available Commands:[/bold]

• [cyan]ask <query>[/cyan] - Ask a question
• [cyan]search <query>[/cyan] - Search documents
• [cyan]tools[/cyan] - Show available tools
• [cyan]clear[/cyan] - Clear conversation history
• [cyan]help[/cyan] - Show this help
• [cyan]quit[/cyan] - Exit the assistant

[bold]Example Queries:[/bold]

• "What's my next meeting?"
• "Summarize today's emails"
• "Find documents about project planning"
• "When is the strategy session next week?"
• "Add a meeting with John tomorrow at 2pm"
"""
    console.print(Panel(help_text, title="Help", border_style="blue"))


def _show_tools():
    """Show available tools."""
    tools = tool_registry.list_tools()
    
    if not tools:
        console.print("[yellow]No tools available.[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tool", style="cyan")
    table.add_column("Description", style="white")
    
    for tool_name in tools:
        tool = tool_registry.get_tool(tool_name)
        if tool:
            table.add_row(tool_name, tool.description)
    
    console.print(Panel(table, title="Available Tools", border_style="blue"))


@cli.command()
@click.argument('query')
@click.option('--max-results', '-n', type=int, default=10, help='Maximum number of results')
@click.option('--source', '-s', help='Filter by source')
@click.option('--json-output', '-j', is_flag=True, help='Output results as JSON')
def search(query: str, max_results: int, source: Optional[str], json_output: bool):
    """Search documents directly (without AI processing)."""
    try:
        # Use the search tool directly
        search_tool = SearchDocumentsTool()
        
        result = search_tool.execute(
            query=query,
            max_results=max_results,
            source_filter=source or ""
        )
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            _display_search_results(result)
    
    except Exception as e:
        logger.error(f"Error during search: {e}")
        if json_output:
            click.echo(json.dumps({'error': str(e)}))
        else:
            console.print(f"[red]Error: {e}[/red]")


def _display_search_results(result: Dict[str, Any]):
    """Display search results."""
    results = result.get('results', [])
    count = result.get('count', 0)
    query = result.get('query', '')
    
    console.print(f"[bold]Search Results for:[/bold] {query}")
    console.print(f"[green]Found {count} results[/green]\n")
    
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    
    for i, res in enumerate(results, 1):
        title = res.get('title', 'Untitled')
        source = res.get('source', 'unknown')
        similarity = res.get('similarity', 0)
        preview = res.get('content_preview', '')
        
        console.print(f"[bold cyan]{i}. {title}[/bold cyan]")
        console.print(f"   [dim]Source: {source} | Similarity: {similarity:.1%}[/dim]")
        console.print(f"   {preview}")
        
        if res.get('url'):
            console.print(f"   [blue]URL: {res['url']}[/blue]")
        
        console.print()


@cli.command()
@click.option('--days', '-d', type=int, default=7, help='Days forward to look')
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
def upcoming(days: int, json_output: bool):
    """Show upcoming calendar events."""
    try:
        tool = GetUpcomingEventsTool()
        result = tool.execute(days_forward=days)
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            _display_calendar_events(result)
    
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        if json_output:
            click.echo(json.dumps({'error': str(e)}))
        else:
            console.print(f"[red]Error: {e}[/red]")


def _display_calendar_events(result: Dict[str, Any]):
    """Display calendar events."""
    events = result.get('events', [])
    count = result.get('count', 0)
    period = result.get('period', '')
    
    console.print(f"[bold]Upcoming Events ({period}):[/bold]")
    console.print(f"[green]Found {count} events[/green]\n")
    
    if not events:
        console.print("[yellow]No upcoming events found.[/yellow]")
        return
    
    for event in events:
        summary = event.get('summary', 'No Title')
        start_time = event.get('start_time', '')
        location = event.get('location', '')
        
        console.print(f"[bold cyan]{summary}[/bold cyan]")
        console.print(f"   [dim]Time: {start_time}[/dim]")
        
        if location:
            console.print(f"   [dim]Location: {location}[/dim]")
        
        if event.get('attendees'):
            attendee_names = [a.get('name', a.get('email', '')) for a in event['attendees'][:3]]
            console.print(f"   [dim]Attendees: {', '.join(attendee_names)}[/dim]")
        
        console.print()


@cli.command()
@click.option('--days', '-d', type=int, default=1, help='Days back to check')
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
def recent_emails(days: int, json_output: bool):
    """Show recent emails."""
    try:
        tool = GetRecentEmailsTool()
        result = tool.execute(days_back=days)
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            _display_emails(result)
    
    except Exception as e:
        logger.error(f"Error getting recent emails: {e}")
        if json_output:
            click.echo(json.dumps({'error': str(e)}))
        else:
            console.print(f"[red]Error: {e}[/red]")


def _display_emails(result: Dict[str, Any]):
    """Display emails."""
    emails = result.get('emails', [])
    count = result.get('count', 0)
    period = result.get('period', '')
    
    console.print(f"[bold]Recent Emails ({period}):[/bold]")
    console.print(f"[green]Found {count} emails[/green]\n")
    
    if not emails:
        console.print("[yellow]No recent emails found.[/yellow]")
        return
    
    for email in emails:
        subject = email.get('subject', 'No Subject')
        from_addr = email.get('from', '')
        date = email.get('date', '')[:16] if email.get('date') else ''  # Show date and time
        snippet = email.get('snippet', '')
        
        console.print(f"[bold cyan]{subject}[/bold cyan]")
        console.print(f"   [dim]From: {from_addr} | {date}[/dim]")
        console.print(f"   {snippet}")
        console.print()


@cli.command()
def status():
    """Show assistant status and configuration."""
    try:
        from ..storage.chroma_manager import ChromaManager
        from ..embeddings.factory import get_default_embedding_service
        
        # Database status
        vector_db = ChromaManager()
        total_docs = vector_db.count()
        
        # Embedding service status
        embedding_service = get_default_embedding_service()
        
        # Tools status
        tools = tool_registry.list_tools()
        
        # Configuration status
        has_openai = bool(config.openai_api_key)
        has_google_creds = bool(config.google_credentials_file)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        table.add_row("Vector Database", "✅ Connected", f"{total_docs} chunks indexed")
        table.add_row("Embedding Service", "✅ Available", f"{embedding_service.model_name} ({embedding_service.dimension}D)")
        table.add_row("Tools", "✅ Loaded", f"{len(tools)} tools available")
        table.add_row("OpenAI API", "✅ Configured" if has_openai else "❌ Not configured", "For advanced AI features")
        table.add_row("Google APIs", "✅ Configured" if has_google_creds else "❌ Not configured", "For Gmail/Calendar access")
        
        console.print(Panel(table, title="Assistant Status", border_style="green"))
        
    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()