"""Claude LLM client implementation."""

from typing import List, Dict, Any, Optional
import anthropic
import json

from .base import BaseLLMClient
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ClaudeLLMClient(BaseLLMClient):
    """Claude LLM client with tool calling support."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize Claude client.
        
        Args:
            api_key: Claude API key. If None, uses config value
            model: Model name. If None, uses config value
        """
        self.api_key = api_key or config.get('claude.api_key')
        self.model = model or config.get('claude.model', 'claude-3-5-sonnet-20241022')
        
        if not self.api_key:
            raise ValueError("Claude API key is required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info(f"Initialized Claude client with model: {self.model}")
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a response from Claude.
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Available tools for function calling
            
        Returns:
            Response dictionary with content and tool calls
        """
        try:
            max_tokens = max_tokens or config.get('claude.max_tokens', 4000)
            
            # Convert tools to Claude format if provided
            claude_tools = self._convert_tools_to_claude_format(tools) if tools else None
            
            # Prepare messages for Claude (Claude doesn't use system messages in the same way)
            claude_messages = self._prepare_messages_for_claude(messages)
            
            # Make the API call
            if claude_tools:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=claude_messages,
                    tools=claude_tools
                )
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=claude_messages
                )
            
            # Process the response
            return self._process_claude_response(response)
            
        except Exception as e:
            logger.error(f"Error generating Claude response: {e}")
            return {
                'content': f"I encountered an error while processing your request: {str(e)}",
                'tool_calls': [],
                'error': str(e)
            }
    
    def _prepare_messages_for_claude(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepare messages for Claude API format.
        
        Args:
            messages: Original messages
            
        Returns:
            Claude-formatted messages
        """
        claude_messages = []
        system_content = ""
        
        for message in messages:
            if message.get('role') == 'system':
                # Claude handles system messages differently
                system_content += message.get('content', '') + "\n"
            else:
                claude_messages.append({
                    'role': message.get('role', 'user'),
                    'content': message.get('content', '')
                })
        
        # If we have system content, prepend it to the first user message
        if system_content and claude_messages:
            first_user_msg = None
            for i, msg in enumerate(claude_messages):
                if msg['role'] == 'user':
                    first_user_msg = i
                    break
            
            if first_user_msg is not None:
                claude_messages[first_user_msg]['content'] = (
                    f"System instructions: {system_content.strip()}\n\n"
                    f"User request: {claude_messages[first_user_msg]['content']}"
                )
        
        return claude_messages
    
    def _convert_tools_to_claude_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style tools to Claude format.
        
        Args:
            tools: OpenAI-style tool definitions
            
        Returns:
            Claude-style tool definitions
        """
        claude_tools = []
        
        for tool in tools:
            if tool.get('type') == 'function':
                function = tool.get('function', {})
                claude_tool = {
                    'name': function.get('name'),
                    'description': function.get('description'),
                    'input_schema': function.get('parameters', {})
                }
                claude_tools.append(claude_tool)
        
        return claude_tools
    
    def _process_claude_response(self, response) -> Dict[str, Any]:
        """Process Claude API response.
        
        Args:
            response: Claude API response
            
        Returns:
            Processed response dictionary
        """
        result = {
            'content': '',
            'tool_calls': [],
            'usage': getattr(response, 'usage', None)
        }
        
        # Extract content and tool calls
        for content_block in response.content:
            if content_block.type == 'text':
                result['content'] += content_block.text
            elif content_block.type == 'tool_use':
                tool_call = {
                    'id': content_block.id,
                    'type': 'function',
                    'function': {
                        'name': content_block.name,
                        'arguments': json.dumps(content_block.input)
                    }
                }
                result['tool_calls'].append(tool_call)
        
        return result
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.model
    
    @property
    def supports_tools(self) -> bool:
        """Check if the model supports tool/function calling."""
        # Claude 3.5 Sonnet and newer models support tools
        return 'claude-3' in self.model.lower() or 'sonnet' in self.model.lower()
    
    def analyze_text(self, text: str, analysis_type: str = "summary") -> str:
        """Use Claude for text analysis tasks.
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis ('summary', 'keywords', 'entities', 'topics')
            
        Returns:
            Analysis result
        """
        prompts = {
            "summary": f"Provide a concise summary of the following text:\n\n{text}",
            "keywords": f"Extract the most important keywords and phrases from this text:\n\n{text}",
            "entities": f"Identify and list all named entities (people, places, organizations, dates, etc.) in this text:\n\n{text}",
            "topics": f"Identify the main topics and themes discussed in this text:\n\n{text}"
        }
        
        prompt = prompts.get(analysis_type, prompts["summary"])
        
        response = self.generate_response(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        return response.get('content', '')