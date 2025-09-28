"""OpenAI LLM client implementation."""

from typing import List, Dict, Any, Optional
from openai import OpenAI

from .base import BaseLLMClient
from ..utils.config import config
from ..utils.logging import get_logger

logger = get_logger(__name__)


class OpenAILLMClient(BaseLLMClient):
    """OpenAI LLM client with tool calling support."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, uses config value
            model: Model name. If None, uses config value
        """
        self.api_key = api_key or config.openai_api_key
        self.model = model or config.openai_model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI client with model: {self.model}")
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a response from OpenAI.
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Available tools for function calling
            
        Returns:
            Response dictionary with content and tool calls
        """
        try:
            max_tokens = max_tokens or 500
            
            # Prepare the API call
            call_params = {
                'model': self.model,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature
            }
            
            # Add tools if provided
            if tools:
                call_params['tools'] = tools
                call_params['tool_choice'] = 'auto'
            
            # Make the API call
            response = self.client.chat.completions.create(**call_params)
            
            # Process the response
            return self._process_openai_response(response)
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return {
                'content': f"I encountered an error while processing your request: {str(e)}",
                'tool_calls': [],
                'error': str(e)
            }
    
    def _process_openai_response(self, response) -> Dict[str, Any]:
        """Process OpenAI API response.
        
        Args:
            response: OpenAI API response
            
        Returns:
            Processed response dictionary
        """
        choice = response.choices[0]
        message = choice.message
        
        result = {
            'content': message.content or '',
            'tool_calls': [],
            'usage': response.usage
        }
        
        # Extract tool calls if present
        if message.tool_calls:
            for tool_call in message.tool_calls:
                result['tool_calls'].append({
                    'id': tool_call.id,
                    'type': tool_call.type,
                    'function': {
                        'name': tool_call.function.name,
                        'arguments': tool_call.function.arguments
                    }
                })
        
        return result
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.model
    
    @property
    def supports_tools(self) -> bool:
        """Check if the model supports tool/function calling."""
        # GPT-4 and newer models support tools
        return 'gpt-4' in self.model.lower() or 'gpt-3.5-turbo' in self.model.lower()