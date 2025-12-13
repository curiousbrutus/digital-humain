"""Unit tests for custom exceptions."""

import pytest
from digital_humain.core.exceptions import (
    DigitalHumainException,
    ToolException,
    ActionException,
    VLMException,
    PlanningException,
    PromptInjectionWarning
)


class TestToolException:
    """Test ToolException functionality."""
    
    def test_tool_exception_creation(self):
        """Test creating a tool exception."""
        exc = ToolException(
            tool_name="file_read",
            message="File not found",
            retryable=True
        )
        
        assert exc.tool_name == "file_read"
        assert exc.retryable is True
        assert "file_read" in str(exc)
        assert "File not found" in str(exc)
    
    def test_tool_exception_non_retryable(self):
        """Test non-retryable tool exception."""
        exc = ToolException(
            tool_name="invalid_tool",
            message="Tool does not exist",
            retryable=False
        )
        
        assert exc.retryable is False
    
    def test_tool_exception_inheritance(self):
        """Test exception inheritance."""
        exc = ToolException("test_tool", "test message")
        
        assert isinstance(exc, DigitalHumainException)
        assert isinstance(exc, Exception)


class TestActionException:
    """Test ActionException functionality."""
    
    def test_action_exception_creation(self):
        """Test creating an action exception."""
        exc = ActionException(
            action_type="click",
            message="Element not found",
            retryable=True
        )
        
        assert exc.action_type == "click"
        assert exc.retryable is True
        assert "click" in str(exc)
    
    def test_action_exception_retryable(self):
        """Test retryable flag."""
        exc = ActionException("type_text", "Keyboard error", retryable=True)
        assert exc.retryable is True
        
        exc2 = ActionException("invalid", "Fatal error", retryable=False)
        assert exc2.retryable is False


class TestVLMException:
    """Test VLMException functionality."""
    
    def test_vlm_exception_creation(self):
        """Test creating a VLM exception."""
        exc = VLMException(
            operation="screen_analysis",
            message="Model inference failed"
        )
        
        assert exc.operation == "screen_analysis"
        assert "screen_analysis" in str(exc)
        assert "Model inference failed" in str(exc)


class TestPlanningException:
    """Test PlanningException functionality."""
    
    def test_planning_exception_creation(self):
        """Test creating a planning exception."""
        exc = PlanningException(
            phase="decomposition",
            message="Unable to break down task"
        )
        
        assert exc.phase == "decomposition"
        assert "decomposition" in str(exc)
        assert "Unable to break down task" in str(exc)
    
    def test_planning_exception_phases(self):
        """Test different planning phases."""
        phases = ["decomposition", "milestone", "replan"]
        
        for phase in phases:
            exc = PlanningException(phase, "test error")
            assert exc.phase == phase


class TestPromptInjectionWarning:
    """Test PromptInjectionWarning functionality."""
    
    def test_prompt_injection_warning_creation(self):
        """Test creating a prompt injection warning."""
        exc = PromptInjectionWarning(
            source="user_input",
            message="Suspicious pattern detected"
        )
        
        assert exc.source == "user_input"
        assert "user_input" in str(exc)
        assert "Suspicious pattern" in str(exc)
    
    def test_prompt_injection_sources(self):
        """Test different injection sources."""
        sources = ["user_input", "screen_content", "api_response"]
        
        for source in sources:
            exc = PromptInjectionWarning(source, "test warning")
            assert exc.source == source
