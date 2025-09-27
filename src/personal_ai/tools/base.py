"""Base tool interface for AI actions."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..utils.logging import get_logger

logger = get_logger(__name__)


class BaseTool(ABC):
    """Abstract base class for AI tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Tool parameters schema."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters.
        
        Returns:
            Dictionary with execution results
        """
        pass
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling format.
        
        Returns:
            OpenAI function definition
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": list(self.parameters.keys())
            }
        }


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, BaseTool] = {}
        logger.info("Initialized tool registry")
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool.
        
        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def get_openai_functions(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI function calling format.
        
        Returns:
            List of OpenAI function definitions
        """
        return [tool.to_openai_function() for tool in self.tools.values()]
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Tool parameters
            
        Returns:
            Execution results
        """
        tool = self.get_tool(name)
        if not tool:
            return {
                'success': False,
                'error': f"Tool '{name}' not found",
                'available_tools': self.list_tools()
            }
        
        try:
            result = tool.execute(**kwargs)
            return {
                'success': True,
                'tool': name,
                'result': result
            }
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return {
                'success': False,
                'tool': name,
                'error': str(e)
            }


# Global tool registry
tool_registry = ToolRegistry()