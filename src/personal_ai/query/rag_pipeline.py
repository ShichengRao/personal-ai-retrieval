"""Retrieval-Augmented Generation (RAG) pipeline for answering queries."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .semantic_search import SemanticSearch
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for query answering."""
    
    def __init__(
        self,
        search_engine: Optional[SemanticSearch] = None,
        llm_client=None
    ):
        """Initialize RAG pipeline.
        
        Args:
            search_engine: Semantic search engine instance
            llm_client: LLM client for generation (OpenAI, etc.)
        """
        self.search_engine = search_engine or SemanticSearch()
        self.llm_client = llm_client
        
        # Initialize LLM client if not provided
        if not self.llm_client:
            self._initialize_llm_client()
        
        logger.info("Initialized RAG pipeline")
    
    def _initialize_llm_client(self):
        """Initialize LLM client based on configuration."""
        self.llm_client = None
        self.llm_type = None
        
        # Try Claude first if API key is available
        claude_key = config.get('claude.api_key')
        if claude_key:
            try:
                import anthropic
                self.llm_client = anthropic.Anthropic(api_key=claude_key)
                self.llm_type = 'claude'
                logger.info("Initialized Claude client")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Claude client: {e}")
        
        # Fall back to OpenAI
        openai_key = config.openai_api_key
        if openai_key:
            try:
                from openai import OpenAI
                self.llm_client = OpenAI(api_key=openai_key)
                self.llm_type = 'openai'
                logger.info("Initialized OpenAI client")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        logger.warning("No LLM API keys found. LLM features will be limited.")
        self.llm_client = None
        self.llm_type = None
    
    def answer_query(
        self,
        query: str,
        max_context_length: int = 4000,
        max_results: int = 5,
        include_sources: bool = True,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Answer a query using retrieval-augmented generation.
        
        Args:
            query: User query
            max_context_length: Maximum length of context to include
            max_results: Maximum number of search results to use
            include_sources: Whether to include source information
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Processing query: '{query}'")
        
        try:
            # Step 1: Retrieve relevant documents
            search_results = self.search_engine.search(
                query=query,
                max_results=max_results,
                include_metadata=True
            )
            
            if not search_results:
                return {
                    'answer': "I couldn't find any relevant information to answer your query.",
                    'sources': [],
                    'confidence': 0.0,
                    'query': query,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Step 2: Prepare context from search results
            context = self._prepare_context(search_results, max_context_length)
            
            # Step 3: Generate answer using LLM
            if self.llm_client:
                answer = self._generate_llm_answer(query, context, conversation_history)
                confidence = self._calculate_confidence(search_results)
            else:
                # Fallback to extractive answer
                answer = self._generate_extractive_answer(query, search_results)
                confidence = 0.7  # Lower confidence for extractive answers
            
            # Step 4: Prepare sources
            sources = self._prepare_sources(search_results) if include_sources else []
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence,
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'context_length': len(context),
                'num_sources': len(search_results)
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'answer': f"I encountered an error while processing your query: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _prepare_context(self, search_results: List[Dict[str, Any]], max_length: int) -> str:
        """Prepare context from search results.
        
        Args:
            search_results: List of search results
            max_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(search_results):
            content = result.get('content', '')
            title = result.get('title', '')
            source = result.get('source', '')
            
            # Format the context entry
            if title:
                entry = f"[Source {i+1}: {title} ({source})]\n{content}\n"
            else:
                entry = f"[Source {i+1} ({source})]\n{content}\n"
            
            # Check if adding this entry would exceed max length
            if current_length + len(entry) > max_length:
                # Try to include a truncated version
                remaining_length = max_length - current_length - 100  # Leave some buffer
                if remaining_length > 200:  # Only include if we have reasonable space
                    truncated_content = content[:remaining_length] + "..."
                    if title:
                        entry = f"[Source {i+1}: {title} ({source})]\n{truncated_content}\n"
                    else:
                        entry = f"[Source {i+1} ({source})]\n{truncated_content}\n"
                    context_parts.append(entry)
                break
            
            context_parts.append(entry)
            current_length += len(entry)
        
        return "\n".join(context_parts)
    
    def _generate_llm_answer(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate answer using LLM.
        
        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous conversation
            
        Returns:
            Generated answer
        """
        try:
            if self.llm_type == 'claude':
                return self._generate_claude_answer(query, context, conversation_history)
            elif self.llm_type == 'openai':
                return self._generate_openai_answer(query, context, conversation_history)
            else:
                return self._generate_extractive_answer(query, [])
                
        except Exception as e:
            logger.error(f"Error generating LLM answer: {e}")
            return self._generate_extractive_answer(query, [])
    
    def _generate_claude_answer(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate answer using Claude.
        
        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous conversation
            
        Returns:
            Generated answer
        """
        # Build conversation for Claude
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-5:]:  # Include last 5 messages
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Build the main prompt with context
        main_prompt = f"""You are a helpful AI assistant that answers questions based on the provided context.

Guidelines:
- Answer based primarily on the provided context
- If the context doesn't contain enough information, say so clearly
- Be concise but comprehensive
- Include specific details from the context when relevant
- If asked about meetings, emails, or calendar events, extract specific details like dates, times, and participants
- For action requests (like "add to calendar"), acknowledge the request but explain that you can suggest the action

Context:
{context}

Question: {query}"""
        
        messages.append({
            "role": "user",
            "content": main_prompt
        })
        
        # Generate response with Claude
        response = self.llm_client.messages.create(
            model=config.get('claude.model', 'claude-3-5-sonnet-20241022'),
            max_tokens=config.get('claude.max_tokens', 500),
            temperature=0.1,  # Low temperature for factual responses
            messages=messages
        )
        
        return response.content[0].text.strip()
    
    def _generate_openai_answer(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate answer using OpenAI.
        
        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous conversation
            
        Returns:
            Generated answer
        """
        # Build messages for the conversation
        messages = []
        
        # System message
        system_prompt = """You are a helpful AI assistant that answers questions based on the provided context. 
        
Guidelines:
- Answer based primarily on the provided context
- If the context doesn't contain enough information, say so clearly
- Be concise but comprehensive
- Include specific details from the context when relevant
- If asked about meetings, emails, or calendar events, extract specific details like dates, times, and participants
- For action requests (like "add to calendar"), acknowledge the request but explain that you can suggest the action

Context:
{context}"""
        
        messages.append({
            "role": "system",
            "content": system_prompt.format(context=context)
        })
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-5:]:  # Include last 5 messages
                messages.append(msg)
        
        # Add current query
        messages.append({
            "role": "user",
            "content": query
        })
        
        # Generate response
        response = self.llm_client.chat.completions.create(
            model=config.openai_model,
            messages=messages,
            max_tokens=500,
            temperature=0.1  # Low temperature for factual responses
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_extractive_answer(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate extractive answer from search results.
        
        Args:
            query: User query
            search_results: Search results
            
        Returns:
            Extractive answer
        """
        if not search_results:
            return "I couldn't find relevant information to answer your query."
        
        # Simple extractive approach: return the most relevant snippet
        best_result = search_results[0]
        content = best_result.get('content', '')
        title = best_result.get('title', '')
        
        # Try to find the most relevant sentence
        sentences = content.split('.')
        query_words = set(query.lower().split())
        
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            sentence_words = set(sentence.lower().split())
            overlap = len(query_words.intersection(sentence_words))
            
            if overlap > best_score:
                best_score = overlap
                best_sentence = sentence
        
        if best_sentence:
            if title:
                return f"Based on '{title}': {best_sentence}."
            else:
                return f"{best_sentence}."
        else:
            # Fallback to first part of content
            preview = content[:300] + "..." if len(content) > 300 else content
            if title:
                return f"From '{title}': {preview}"
            else:
                return preview
    
    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results.
        
        Args:
            search_results: Search results
            
        Returns:
            Confidence score between 0 and 1
        """
        if not search_results:
            return 0.0
        
        # Base confidence on similarity scores
        similarities = [result.get('similarity', 0.0) for result in search_results]
        avg_similarity = sum(similarities) / len(similarities)
        
        # Boost confidence if we have multiple good results
        if len(search_results) >= 3 and avg_similarity > 0.7:
            return min(avg_similarity + 0.1, 1.0)
        
        return avg_similarity
    
    def _prepare_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare source information from search results.
        
        Args:
            search_results: Search results
            
        Returns:
            List of source dictionaries
        """
        sources = []
        
        for result in search_results:
            source = {
                'title': result.get('title', 'Untitled'),
                'source': result.get('source', 'unknown'),
                'url': result.get('url', ''),
                'similarity': result.get('similarity', 0.0),
                'date': result.get('date', ''),
                'snippet': result.get('content', '')[:200] + "..." if len(result.get('content', '')) > 200 else result.get('content', '')
            }
            sources.append(source)
        
        return sources
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze query intent to determine appropriate response strategy.
        
        Args:
            query: User query
            
        Returns:
            Intent analysis results
        """
        query_lower = query.lower()
        
        intent = {
            'type': 'search',  # Default intent
            'entities': [],
            'time_sensitive': False,
            'action_required': False,
            'confidence': 0.8
        }
        
        # Check for action intents
        action_keywords = ['add', 'create', 'schedule', 'send', 'delete', 'update', 'remind']
        if any(keyword in query_lower for keyword in action_keywords):
            intent['type'] = 'action'
            intent['action_required'] = True
        
        # Check for time-sensitive queries
        time_keywords = ['today', 'tomorrow', 'next week', 'this week', 'upcoming', 'recent']
        if any(keyword in query_lower for keyword in time_keywords):
            intent['time_sensitive'] = True
        
        # Check for specific entity types
        if 'email' in query_lower or 'mail' in query_lower:
            intent['entities'].append('email')
        
        if 'meeting' in query_lower or 'calendar' in query_lower or 'appointment' in query_lower:
            intent['entities'].append('calendar')
        
        if 'document' in query_lower or 'file' in query_lower:
            intent['entities'].append('document')
        
        return intent