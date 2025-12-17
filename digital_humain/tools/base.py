"""Base tool interface and registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from loguru import logger


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolMetadata(BaseModel):
    """Tool metadata."""
    name: str
    description: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    returns: str = "Any"


class ToolResult(BaseModel):
    """Result of tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseTool(ABC):
    """
    Base class for tools that agents can use.
    
    Tools provide specific capabilities to agents.
    """
    
    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Returns:
            Dictionary with 'success' flag and 'result' or 'error'
        """
        pass
    
    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate tool parameters.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if valid
        """
        metadata = self.get_metadata()
        
        for param in metadata.parameters:
            if param.required and param.name not in kwargs:
                logger.error(f"Missing required parameter: {param.name}")
                return False
        
        return True


class ToolRegistry:
    """
    Registry for managing tools.
    
    Provides tool lookup and execution.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        logger.info("Initialized ToolRegistry")
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
        """
        metadata = tool.get_metadata()
        tool_name = metadata.name
        
        if tool_name in self._tools:
            logger.warning(f"Tool {tool_name} already registered, replacing")
        
        self._tools[tool_name] = tool
        logger.info(f"Registered tool: {tool_name}")
    
    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            tool_name: Name of tool to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            return True
        
        logger.warning(f"Tool not found: {tool_name}")
        return False
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of tool to retrieve
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a tool.
        
        Args:
            tool_name: Name of tool
            
        Returns:
            Tool metadata or None if not found
        """
        tool = self.get(tool_name)
        if tool:
            return tool.get_metadata()
        return None
    
    def list_tools_metadata(self) -> List[ToolMetadata]:
        """
        List metadata for all registered tools.
        
        Returns:
            List of tool metadata
        """
        return [tool.get_metadata() for tool in self._tools.values()]
    
    def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters
            
        Returns:
            Execution result
        """
        tool = self.get(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}"
            }
        
        if not tool.validate_parameters(**kwargs):
            return {
                "success": False,
                "error": f"Invalid parameters for tool: {tool_name}"
            }
        
        try:
            result = tool.execute(**kwargs)
            logger.debug(f"Tool executed: {tool_name}")
            return result
        
        except Exception as e:
            logger.exception(f"Tool execution failed: {tool_name}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear(self) -> None:
        """Clear all registered tools."""
        count = len(self._tools)
        self._tools.clear()
        logger.info(f"Cleared {count} tools from registry")
