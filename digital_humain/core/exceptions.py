"""Custom exceptions for Digital Humain framework."""


class DigitalHumainException(Exception):
    """Base exception for Digital Humain."""
    pass


class ToolException(DigitalHumainException):
    """
    Exception raised when a tool execution fails.
    
    This exception is used for explicit error handling in LangGraph,
    allowing the state machine to route failures to dedicated recovery nodes.
    """
    
    def __init__(self, tool_name: str, message: str, retryable: bool = True):
        """
        Initialize tool exception.
        
        Args:
            tool_name: Name of the tool that failed
            message: Error message
            retryable: Whether the operation can be retried
        """
        self.tool_name = tool_name
        self.retryable = retryable
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class ActionException(DigitalHumainException):
    """
    Exception raised when a GUI action fails.
    
    Used for handling PyAutoGUI and other action execution failures.
    """
    
    def __init__(self, action_type: str, message: str, retryable: bool = True):
        """
        Initialize action exception.
        
        Args:
            action_type: Type of action that failed
            message: Error message
            retryable: Whether the action can be retried
        """
        self.action_type = action_type
        self.retryable = retryable
        super().__init__(f"Action '{action_type}' failed: {message}")


class VLMException(DigitalHumainException):
    """
    Exception raised when VLM operations fail.
    
    Used for screen analysis and visual understanding failures.
    """
    
    def __init__(self, operation: str, message: str):
        """
        Initialize VLM exception.
        
        Args:
            operation: VLM operation that failed
            message: Error message
        """
        self.operation = operation
        super().__init__(f"VLM operation '{operation}' failed: {message}")


class PlanningException(DigitalHumainException):
    """
    Exception raised when planning or reasoning fails.
    
    Used for LLM planning errors in hierarchical planning.
    """
    
    def __init__(self, phase: str, message: str):
        """
        Initialize planning exception.
        
        Args:
            phase: Planning phase that failed (e.g., 'decomposition', 'milestone')
            message: Error message
        """
        self.phase = phase
        super().__init__(f"Planning failed in phase '{phase}': {message}")


class PromptInjectionWarning(DigitalHumainException):
    """
    Warning raised when potential prompt injection is detected.
    
    Used for security monitoring and defensive measures.
    """
    
    def __init__(self, source: str, message: str):
        """
        Initialize prompt injection warning.
        
        Args:
            source: Source of potential injection (e.g., 'user_input', 'screen_content')
            message: Warning message
        """
        self.source = source
        super().__init__(f"Potential prompt injection from '{source}': {message}")
