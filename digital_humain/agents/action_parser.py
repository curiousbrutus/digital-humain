"""Action parsing helpers for extracting and executing intents from reasoning."""

import re
import subprocess
import platform
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger


class ActionIntent:
    """Parsed action intent from reasoning text."""
    
    def __init__(
        self,
        action_type: str,
        confidence: float = 1.0,
        params: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ):
        self.action_type = action_type
        self.confidence = confidence
        self.params = params or {}
        self.reason = reason or ""
    
    def __repr__(self):
        return f"ActionIntent(type={self.action_type}, confidence={self.confidence}, params={self.params})"


class AppLauncher:
    """Safe application launcher with allowlist."""
    
    ALLOWED_WINDOWS_APPS = {
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "mspaint": "mspaint.exe",
        "paint": "mspaint.exe",
        "explorer": "explorer.exe",
    }
    
    ALLOWED_LINUX_APPS = {
        "gedit": "gedit",
        "gnome-calculator": "gnome-calculator",
        "calc": "gnome-calculator",
        "calculator": "gnome-calculator",
        "nautilus": "nautilus",
        "files": "nautilus",
    }
    
    ALLOWED_MAC_APPS = {
        "textedit": "open -a TextEdit",
        "calculator": "open -a Calculator",
        "calc": "open -a Calculator",
        "finder": "open -a Finder",
    }
    
    @classmethod
    def get_allowed_apps(cls) -> Dict[str, str]:
        """Get allowed apps for current platform."""
        system = platform.system()
        if system == "Windows":
            return cls.ALLOWED_WINDOWS_APPS
        elif system == "Linux":
            return cls.ALLOWED_LINUX_APPS
        elif system == "Darwin":
            return cls.ALLOWED_MAC_APPS
        return {}
    
    @classmethod
    def launch_app(cls, app_name: str) -> Dict[str, Any]:
        """
        Launch an application from the allowlist.
        
        Args:
            app_name: Name of the app to launch (e.g., "notepad", "calc")
            
        Returns:
            Result dictionary with success status
        """
        app_name_lower = app_name.lower().strip()
        allowed = cls.get_allowed_apps()
        
        if app_name_lower not in allowed:
            logger.warning(f"App '{app_name}' not in allowlist. Allowed: {list(allowed.keys())}")
            return {
                "action": "launch_app",
                "success": False,
                "error": f"App '{app_name}' not allowed. Allowed apps: {', '.join(allowed.keys())}",
                "app_name": app_name
            }
        
        command = allowed[app_name_lower]
        try:
            # Split Mac commands into proper list format for security
            if platform.system() == "Darwin" and isinstance(command, str):
                cmd_parts = command.split()
                subprocess.Popen(cmd_parts)
            elif isinstance(command, str):
                subprocess.Popen([command])
            else:
                subprocess.Popen(command)
            logger.info(f"Launched app: {app_name} ({command})")
            return {
                "action": "launch_app",
                "success": True,
                "app_name": app_name,
                "command": command
            }
        except Exception as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            return {
                "action": "launch_app",
                "success": False,
                "error": str(e),
                "app_name": app_name
            }


class ActionParser:
    """Parse reasoning text to extract actionable intents."""
    
    KEY_MAPPINGS = {
        "enter": "enter",
        "return": "enter",
        "tab": "tab",
        "escape": "esc",
        "esc": "esc",
        "space": "space",
        "spacebar": "space",
        "backspace": "backspace",
        "delete": "delete",
        "del": "delete",
        "windows": "win",
        "super": "win",
        "cmd": "command",
        "command": "command",
        "control": "ctrl",
        "ctrl": "ctrl",
        "alt": "alt",
        "shift": "shift",
    }
    
    @classmethod
    def extract_quoted_text(cls, text: str) -> Optional[str]:
        """
        Extract text within quotes (single or double).
        
        Args:
            text: Text to search
            
        Returns:
            Quoted text if found, None otherwise
        """
        # Try double quotes first
        match = re.search(r'"([^"]+)"', text)
        if match:
            return match.group(1)
        
        # Try single quotes
        match = re.search(r"'([^']+)'", text)
        if match:
            return match.group(1)
        
        return None
    
    @classmethod
    def parse_typing_intent(
        cls,
        reasoning: str,
        context: Optional[Dict[str, Any]] = None,
        task: Optional[str] = None
    ) -> ActionIntent:
        """
        Parse typing intent from reasoning.
        
        Prefers quoted text, falls back to context or task.
        Never uses generic placeholders.
        
        Args:
            reasoning: Reasoning text
            context: Optional context dictionary
            task: Optional task description
            
        Returns:
            ActionIntent for typing
        """
        reasoning_lower = reasoning.lower()
        
        # Extract quoted text first
        quoted = cls.extract_quoted_text(reasoning)
        if quoted:
            return ActionIntent(
                action_type="type_text",
                confidence=0.9,
                params={"text": quoted},
                reason="Extracted from quoted text in reasoning"
            )
        
        # Fall back to context
        if context and "input_text" in context:
            text = context["input_text"]
            return ActionIntent(
                action_type="type_text",
                confidence=0.7,
                params={"text": text},
                reason="Using input_text from context"
            )
        
        # Fall back to task description
        if task:
            # Try to extract meaningful content from task
            task_words = task.split()
            if len(task_words) > 3:
                # Use task as-is if it's substantial
                return ActionIntent(
                    action_type="type_text",
                    confidence=0.5,
                    params={"text": task},
                    reason="Using task description as typing content"
                )
        
        # No actionable text found - return no_action
        return ActionIntent(
            action_type="no_action",
            confidence=1.0,
            params={},
            reason="No specific text to type found in reasoning, context, or task"
        )
    
    @classmethod
    def parse_key_press(cls, reasoning: str) -> Optional[ActionIntent]:
        """
        Parse key press intent from reasoning.
        
        Args:
            reasoning: Reasoning text
            
        Returns:
            ActionIntent for key press, or None if not found
        """
        reasoning_lower = reasoning.lower()
        
        # Look for press/hit patterns
        patterns = [
            r'(?:press|hit|push)\s+(?:the\s+)?(\w+)(?:\s+key)?',
            r'(?:tap|strike)\s+(?:the\s+)?(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, reasoning_lower)
            if match:
                key_name = match.group(1)
                # Map to pyautogui key name
                mapped_key = cls.KEY_MAPPINGS.get(key_name, key_name)
                
                return ActionIntent(
                    action_type="press_key",
                    confidence=0.85,
                    params={"key": mapped_key},
                    reason=f"Extracted key press: {key_name} -> {mapped_key}"
                )
        
        return None
    
    @classmethod
    def parse_app_launch(cls, reasoning: str) -> Optional[ActionIntent]:
        """
        Parse app launch intent from reasoning.
        
        Args:
            reasoning: Reasoning text
            
        Returns:
            ActionIntent for app launch, or None if not found
        """
        reasoning_lower = reasoning.lower()
        allowed_apps = AppLauncher.get_allowed_apps()
        
        # Check for app names in reasoning
        for app_name in allowed_apps.keys():
            if app_name in reasoning_lower:
                # Check context to confirm it's a launch intent
                launch_keywords = ["open", "launch", "start", "run", "execute"]
                if any(kw in reasoning_lower for kw in launch_keywords) or "open" in reasoning_lower:
                    return ActionIntent(
                        action_type="launch_app",
                        confidence=0.9,
                        params={"app_name": app_name},
                        reason=f"Found app name '{app_name}' with launch intent"
                    )
                # Even without explicit launch keyword, if app is mentioned, likely intent to open
                elif reasoning_lower.startswith(app_name) or f" {app_name}" in reasoning_lower:
                    return ActionIntent(
                        action_type="launch_app",
                        confidence=0.7,
                        params={"app_name": app_name},
                        reason=f"App name '{app_name}' found in reasoning"
                    )
        
        return None
    
    @classmethod
    def parse_click_intent(cls, reasoning: str) -> Optional[ActionIntent]:
        """
        Parse click intent from reasoning.
        
        Args:
            reasoning: Reasoning text
            
        Returns:
            ActionIntent for click, or None if not found
        """
        reasoning_lower = reasoning.lower()
        
        if "click" in reasoning_lower:
            # Try to extract coordinates or element description
            coord_match = re.search(r'(?:at|on)\s*\(?(\d+)\s*,\s*(\d+)\)?', reasoning_lower)
            if coord_match:
                x, y = int(coord_match.group(1)), int(coord_match.group(2))
                return ActionIntent(
                    action_type="click",
                    confidence=0.9,
                    params={"x": x, "y": y},
                    reason="Extracted coordinates from reasoning"
                )
            
            # Generic click without coordinates
            return ActionIntent(
                action_type="click",
                confidence=0.6,
                params={},
                reason="Click action mentioned without specific coordinates"
            )
        
        return None
    
    @classmethod
    def parse(
        cls,
        reasoning: str,
        context: Optional[Dict[str, Any]] = None,
        task: Optional[str] = None
    ) -> ActionIntent:
        """
        Parse reasoning to extract action intent.
        
        Args:
            reasoning: Reasoning text from LLM
            context: Optional context dictionary
            task: Optional task description
            
        Returns:
            ActionIntent with type, confidence, and parameters
        """
        if not reasoning or not reasoning.strip():
            return ActionIntent(
                action_type="no_action",
                confidence=1.0,
                reason="Empty reasoning provided"
            )
        
        reasoning_lower = reasoning.lower()
        
        # Check for task completion indicators first
        if any(word in reasoning_lower for word in ["complete", "done", "finish", "success", "accomplished"]):
            return ActionIntent(
                action_type="task_complete",
                confidence=0.9,
                reason="Task completion indicated in reasoning"
            )
        
        # Try to parse app launch
        app_intent = cls.parse_app_launch(reasoning)
        if app_intent:
            return app_intent
        
        # Try to parse key press
        key_intent = cls.parse_key_press(reasoning)
        if key_intent:
            return key_intent
        
        # Try to parse typing intent
        if any(word in reasoning_lower for word in ["type", "enter", "input", "write"]):
            return cls.parse_typing_intent(reasoning, context, task)
        
        # Try to parse click
        click_intent = cls.parse_click_intent(reasoning)
        if click_intent:
            return click_intent
        
        # Check for screen analysis
        if any(word in reasoning_lower for word in ["analyze", "look", "check", "see", "observe", "examine"]):
            return ActionIntent(
                action_type="analyze_screen",
                confidence=0.8,
                reason="Screen analysis action detected"
            )
        
        # Check for wait/pause
        if any(word in reasoning_lower for word in ["wait", "pause", "delay"]):
            # Try to extract duration
            duration_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:second|sec|s)', reasoning_lower)
            duration = float(duration_match.group(1)) if duration_match else 1.0
            return ActionIntent(
                action_type="wait",
                confidence=0.9,
                params={"duration": duration},
                reason="Wait action detected"
            )
        
        # No actionable intent found
        return ActionIntent(
            action_type="no_action",
            confidence=1.0,
            reason="No clear actionable command found in reasoning"
        )
