"""Unit tests for action parsing helpers."""

import pytest
import platform

# Import directly to avoid GUI dependencies
from digital_humain.agents.action_parser import (
    ActionParser,
    ActionIntent,
    AppLauncher
)


class TestActionIntent:
    """Test ActionIntent class."""
    
    def test_action_intent_creation(self):
        """Test creating ActionIntent."""
        intent = ActionIntent(
            action_type="type_text",
            confidence=0.9,
            params={"text": "hello"},
            reason="test"
        )
        
        assert intent.action_type == "type_text"
        assert intent.confidence == 0.9
        assert intent.params["text"] == "hello"
        assert intent.reason == "test"
    
    def test_action_intent_repr(self):
        """Test ActionIntent string representation."""
        intent = ActionIntent("click", 0.8, {"x": 100})
        repr_str = repr(intent)
        
        assert "click" in repr_str
        assert "0.8" in repr_str


class TestAppLauncher:
    """Test AppLauncher functionality."""
    
    def test_get_allowed_apps(self):
        """Test getting allowed apps for current platform."""
        allowed = AppLauncher.get_allowed_apps()
        
        assert isinstance(allowed, dict)
        assert len(allowed) > 0
        
        # Should have notepad on Windows, gedit on Linux, or textedit on Mac
        system = platform.system()
        if system == "Windows":
            assert "notepad" in allowed
            assert "calc" in allowed
        elif system == "Linux":
            assert "gedit" in allowed or "calc" in allowed
        elif system == "Darwin":
            assert "textedit" in allowed or "calculator" in allowed
    
    def test_launch_app_not_in_allowlist(self):
        """Test launching app not in allowlist."""
        result = AppLauncher.launch_app("evil_app_12345")
        
        assert result["success"] is False
        assert "not allowed" in result["error"].lower()
        assert result["action"] == "launch_app"


class TestActionParser:
    """Test ActionParser functionality."""
    
    def test_extract_quoted_text_double_quotes(self):
        """Test extracting text with double quotes."""
        text = 'Please type "Hello World" now'
        result = ActionParser.extract_quoted_text(text)
        
        assert result == "Hello World"
    
    def test_extract_quoted_text_single_quotes(self):
        """Test extracting text with single quotes."""
        text = "Type 'Test Message' here"
        result = ActionParser.extract_quoted_text(text)
        
        assert result == "Test Message"
    
    def test_extract_quoted_text_no_quotes(self):
        """Test extracting when no quotes present."""
        text = "Type something here"
        result = ActionParser.extract_quoted_text(text)
        
        assert result is None
    
    def test_parse_typing_with_quotes(self):
        """Test parsing typing intent with quoted text."""
        reasoning = 'I should type "Dear Steve Jobs" in the text field'
        intent = ActionParser.parse_typing_intent(reasoning)
        
        assert intent.action_type == "type_text"
        assert intent.params["text"] == "Dear Steve Jobs"
        assert intent.confidence > 0.8
    
    def test_parse_typing_with_context(self):
        """Test parsing typing intent with context fallback."""
        reasoning = "Type the input text"
        context = {"input_text": "Context text here"}
        intent = ActionParser.parse_typing_intent(reasoning, context=context)
        
        assert intent.action_type == "type_text"
        assert intent.params["text"] == "Context text here"
    
    def test_parse_typing_with_task_fallback(self):
        """Test parsing typing intent with letter task fallback."""
        reasoning = "Type the message"
        task = "Write a letter to Bob"
        intent = ActionParser.parse_typing_intent(reasoning, task=task)
        
        assert intent.action_type == "type_text"
        assert "bob" in intent.params["text"].lower()
    
    def test_parse_typing_no_content(self):
        """Test parsing typing intent with no actionable content."""
        reasoning = "Type something"
        intent = ActionParser.parse_typing_intent(reasoning)
        
        # Should return no_action when no content found
        assert intent.action_type == "no_action"
        assert "no specific text" in intent.reason.lower()
    
    def test_parse_key_press_enter(self):
        """Test parsing Enter key press."""
        reasoning = "Press the Enter key to submit"
        intent = ActionParser.parse_key_press(reasoning)
        
        assert intent is not None
        assert intent.action_type == "press_key"
        assert intent.params["key"] == "enter"
    
    def test_parse_key_press_tab(self):
        """Test parsing Tab key press."""
        reasoning = "Hit tab to move to next field"
        intent = ActionParser.parse_key_press(reasoning)
        
        assert intent is not None
        assert intent.action_type == "press_key"
        assert intent.params["key"] == "tab"
    
    def test_parse_key_press_not_found(self):
        """Test parsing when no key press found."""
        reasoning = "Move the mouse cursor"
        intent = ActionParser.parse_key_press(reasoning)
        
        assert intent is None
    
    def test_parse_app_launch_notepad(self):
        """Test parsing app launch intent (platform-specific)."""
        # Use platform-appropriate app name
        system = platform.system()
        if system == "Windows":
            reasoning = "Open notepad to write the message"
            app_name = "notepad"
        elif system == "Linux":
            reasoning = "Open gedit to write the message"
            app_name = "gedit"
        else:  # Darwin/Mac
            reasoning = "Open textedit to write the message"
            app_name = "textedit"
        
        intent = ActionParser.parse_app_launch(reasoning)
        
        assert intent is not None
        assert intent.action_type == "launch_app"
        assert app_name in intent.params.get("app_name", "").lower()
    
    def test_parse_app_launch_calculator(self):
        """Test parsing calculator launch intent."""
        reasoning = "Launch the calculator app"
        intent = ActionParser.parse_app_launch(reasoning)
        
        assert intent is not None
        assert intent.action_type == "launch_app"
        assert "calc" in intent.params.get("app_name", "").lower()
    
    def test_parse_click_with_coordinates(self):
        """Test parsing click with coordinates."""
        reasoning = "Click at position (500, 300)"
        intent = ActionParser.parse_click_intent(reasoning)
        
        assert intent is not None
        assert intent.action_type == "click"
        assert intent.params["x"] == 500
        assert intent.params["y"] == 300
    
    def test_parse_click_without_coordinates(self):
        """Test parsing click without coordinates."""
        reasoning = "Click the button"
        intent = ActionParser.parse_click_intent(reasoning)
        
        assert intent is not None
        assert intent.action_type == "click"
        assert "x" not in intent.params or intent.params["x"] is None
    
    def test_parse_empty_reasoning(self):
        """Test parsing empty reasoning."""
        intent = ActionParser.parse("")
        
        assert intent.action_type == "no_action"
        assert "empty" in intent.reason.lower()
    
    def test_parse_task_completion(self):
        """Test parsing task completion."""
        reasoning = "The task is now complete and successful"
        intent = ActionParser.parse(reasoning)
        
        assert intent.action_type == "task_complete"
    
    def test_parse_screen_analysis(self):
        """Test parsing screen analysis intent."""
        reasoning = "Let me analyze the screen to see what's available"
        intent = ActionParser.parse(reasoning)
        
        assert intent.action_type == "analyze_screen"
    
    def test_parse_wait_with_duration(self):
        """Test parsing wait with duration."""
        reasoning = "Wait for 2.5 seconds before proceeding"
        intent = ActionParser.parse(reasoning)
        
        assert intent.action_type == "wait"
        assert intent.params["duration"] == 2.5
    
    def test_parse_wait_default_duration(self):
        """Test parsing wait with default duration."""
        reasoning = "Wait a moment"
        intent = ActionParser.parse(reasoning)
        
        assert intent.action_type == "wait"
        assert intent.params["duration"] == 1.0
    
    def test_parse_full_workflow(self):
        """Test parsing a complete workflow."""
        # Test app launch (platform-specific)
        system = platform.system()
        if system == "Windows":
            intent1 = ActionParser.parse("Open notepad application")
        elif system == "Linux":
            intent1 = ActionParser.parse("Open gedit application")
        else:
            intent1 = ActionParser.parse("Open textedit application")
        assert intent1.action_type == "launch_app"
        
        # Test typing with quotes
        intent2 = ActionParser.parse('Type "Hello World" in the editor', task="Write a message")
        assert intent2.action_type == "type_text"
        assert intent2.params["text"] == "Hello World"
        
        # Test key press
        intent3 = ActionParser.parse("Press Enter to create new line")
        assert intent3.action_type == "press_key"
        assert intent3.params["key"] == "enter"
        
        # Test completion
        intent4 = ActionParser.parse("Task is complete")
        assert intent4.action_type == "task_complete"
    
    def test_parse_no_actionable_command(self):
        """Test parsing when no actionable command found."""
        reasoning = "I am thinking about what to do next"
        intent = ActionParser.parse(reasoning)
        
        assert intent.action_type == "no_action"
        assert intent.confidence == 1.0
