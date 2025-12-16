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
    """Safe application launcher with allowlist and auto-discovery."""
    
    # Cached discovered apps
    _discovered_apps = None
    
    @classmethod
    def refresh_discovered_apps(cls):
        """Force refresh of discovered desktop applications."""
        cls._discovered_apps = cls.discover_desktop_apps()
        logger.info(f"Refreshed app discovery: {len(cls._discovered_apps)} apps found")
    
    ALLOWED_WINDOWS_APPS = {
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "mspaint": "mspaint.exe",
        "paint": "mspaint.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "terminal": "wt.exe",  # Windows Terminal
    }
    
    ALLOWED_LINUX_APPS = {
        # Text editors - "notepad" maps to gedit on Linux
        "notepad": "gedit",  # Cross-platform alias
        "gedit": "gedit",
        "kate": "kate",
        "xed": "xed",
        "mousepad": "mousepad",
        "pluma": "pluma",
        "text editor": "gedit",
        # Calculators
        "gnome-calculator": "gnome-calculator",
        "calc": "gnome-calculator",
        "calculator": "gnome-calculator",
        "kcalc": "kcalc",
        # File managers
        "nautilus": "nautilus",
        "files": "nautilus",
        "dolphin": "dolphin",
        "nemo": "nemo",
        "thunar": "thunar",
        # Terminal
        "terminal": "gnome-terminal",
        "gnome-terminal": "gnome-terminal",
        "konsole": "konsole",
        "xterm": "xterm",
        # Browsers
        "firefox": "firefox",
        "chromium": "chromium-browser",
    }
    
    ALLOWED_MAC_APPS = {
        "textedit": "open -a TextEdit",
        "calculator": "open -a Calculator",
        "calc": "open -a Calculator",
        "finder": "open -a Finder",
    }
    
    @classmethod
    def discover_desktop_apps(cls) -> Dict[str, str]:
        """Discover applications on Desktop and common locations."""
        import os
        from pathlib import Path
        
        discovered = {}
        system = platform.system()
        
        if system == "Windows":
            # Search locations
            search_paths = [
                Path.home() / "Desktop",
                Path.home() / "OneDrive" / "Desktop",
                Path("C:\\Program Files"),
                Path("C:\\Program Files (x86)"),
            ]
            
            for search_path in search_paths:
                if not search_path.exists():
                    continue
                
                try:
                    # Find .exe and .lnk files
                    for item in search_path.iterdir():
                        if item.is_file() and item.suffix.lower() in ['.exe', '.lnk']:
                            # Use stem (filename without extension) as key
                            name_key = item.stem.lower()
                            discovered[name_key] = str(item)
                            logger.debug(f"Discovered app: {name_key} -> {item}")
                        elif item.is_dir() and search_path.name.startswith("Program"):
                            # Check one level deep in Program Files
                            try:
                                for subitem in item.iterdir():
                                    if subitem.is_file() and subitem.suffix.lower() == '.exe':
                                        name_key = subitem.stem.lower()
                                        if name_key not in discovered:  # Don't override Desktop items
                                            discovered[name_key] = str(subitem)
                                            logger.debug(f"Discovered app: {name_key} -> {subitem}")
                            except (PermissionError, OSError):
                                continue
                except (PermissionError, OSError) as e:
                    logger.debug(f"Could not scan {search_path}: {e}")
        
        logger.info(f"Discovered {len(discovered)} applications")
        return discovered
    
    @classmethod
    def get_allowed_apps(cls) -> Dict[str, str]:
        """Get allowed apps for current platform, including discovered apps."""
        # Cache discovered apps
        if cls._discovered_apps is None:
            cls._discovered_apps = cls.discover_desktop_apps()
        
        system = platform.system()
        base_apps = {}
        if system == "Windows":
            base_apps = cls.ALLOWED_WINDOWS_APPS.copy()
        elif system == "Linux":
            base_apps = cls.ALLOWED_LINUX_APPS.copy()
        elif system == "Darwin":
            base_apps = cls.ALLOWED_MAC_APPS.copy()
        
        # Merge discovered apps
        base_apps.update(cls._discovered_apps)
        return base_apps
    
    @classmethod
    def launch_app(cls, app_name: str) -> Dict[str, Any]:
        """
        Launch an application from the allowlist.
        
        Args:
            app_name: Name of the app to launch (e.g., "notepad", "calc", "bizmed")
            
        Returns:
            Result dictionary with success status
        """
        app_name_lower = app_name.lower().strip()
        allowed = cls.get_allowed_apps()
        
        # Try exact match first
        command = allowed.get(app_name_lower)
        
        # If not found, try fuzzy matching (partial name)
        if not command:
            matches = [k for k in allowed.keys() if app_name_lower in k or k in app_name_lower]
            if matches:
                command = allowed[matches[0]]
                logger.info(f"Fuzzy matched '{app_name}' to '{matches[0]}'")
                app_name_lower = matches[0]
        
        if not command:
            available = list(allowed.keys())[:20]  # Show first 20
            logger.warning(f"App '{app_name}' not found. Available: {available}")
            return {
                "action": "launch_app",
                "success": False,
                "error": f"App '{app_name}' not found. Available apps include: {', '.join(available)}",
                "app_name": app_name
            }
        
        try:
            # Handle .lnk shortcuts on Windows
            if platform.system() == "Windows" and command.endswith('.lnk'):
                import os
                os.startfile(command)
            # Split Mac commands into proper list format for security
            elif platform.system() == "Darwin" and isinstance(command, str):
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
                "app_name": app_name_lower,
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
        If task mentions writing a letter, generate appropriate text.
        
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
        
        # Check if task mentions writing a letter to someone
        if task:
            task_lower = task.lower()
            # Check for letter writing patterns
            letter_match = re.search(r'(?:write|type)\s+(?:a\s+)?letter\s+to\s+(\w+(?:\s+\w+)?)', task_lower)
            if letter_match:
                recipient = letter_match.group(1).title()
                # Check for word count requirement
                word_count_match = re.search(r'(\d+)\s*words?', task_lower)
                if word_count_match:
                    word_count = int(word_count_match.group(1))
                    # Generate a letter of approximately the right length
                    if word_count <= 10:
                        text = f"Dear {recipient}, thank you for inspiring us all. Best regards."
                    elif word_count <= 20:
                        text = f"Dear {recipient}, your vision and innovation changed the world forever. Thank you for everything you have done. Best regards."
                    else:
                        text = f"Dear {recipient}, I wanted to write to express my deep gratitude for your incredible contributions to technology and innovation. Your vision has changed the world in countless ways. Thank you."
                else:
                    text = f"Dear {recipient}, thank you for your incredible vision and innovation. Best regards."
                
                return ActionIntent(
                    action_type="type_text",
                    confidence=0.8,
                    params={"text": text},
                    reason=f"Generated letter to {recipient} based on task"
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
                launch_keywords = ["open", "launch", "start", "run", "execute", "must be opened", "need to open", "should open", "go to"]
                if any(kw in reasoning_lower for kw in launch_keywords):
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
        
        # Check for task completion indicators - must be ACTUAL completion, not intent
        # Avoid false positives like "to complete the task" (future intent)
        completion_phrases = [
            "task is complete", "task is done", "task complete", "task done",
            "completed the task", "finished the task", "accomplished the task",
            "the letter has been written", "the letter has been typed",
            "successfully written", "successfully typed", "successfully completed",
            "i have finished", "i have completed", "have been written",
            "task is now complete", "task is now done",
            "this completes the task", "that completes the task"
        ]
        # These phrases indicate the task is NOT yet complete
        future_intent_phrases = ["to complete the task", "to complete this", "in order to complete", "should be", "will be", "next step"]
        
        has_completion = any(phrase in reasoning_lower for phrase in completion_phrases)
        has_future_intent = any(phrase in reasoning_lower for phrase in future_intent_phrases)
        
        if has_completion and not has_future_intent:
            return ActionIntent(
                action_type="task_complete",
                confidence=0.9,
                reason="Task completion indicated in reasoning"
            )
        
        # PRIORITY 1: Check for EXPLICIT action commands in "Next action:" format
        # This takes precedence over implicit intent detection
        # Pattern for "launch_app/open <app>" or just "open <app>"
        launch_action_match = re.search(
            r'\*{0,2}next\s+action[:\*]{1,3}\s*(?:launch_app[/\s]+)?(?:open|launch|start)\s+(\w+)',
            reasoning_lower
        )
        if launch_action_match:
            app_name = launch_action_match.group(1)
            allowed_apps = AppLauncher.get_allowed_apps()
            if app_name in allowed_apps:
                return ActionIntent(
                    action_type="launch_app",
                    confidence=0.95,
                    params={"app_name": app_name},
                    reason=f"Explicit launch action from Next action: {app_name}"
                )
        
        # Pattern for "type_text/type 'text'" or "type 'text'"
        type_action_match = re.search(
            r'\*{0,2}next\s+action[:\*]{1,3}\s*(?:type_text[/\s]+)?type',
            reasoning_lower
        )
        if type_action_match:
            quoted = cls.extract_quoted_text(reasoning)
            if quoted:
                return ActionIntent(
                    action_type="type_text",
                    confidence=0.95,
                    params={"text": quoted},
                    reason="Explicit type action with quoted text"
                )
        
        # PRIORITY 2: Check for direct "I will open/launch X" patterns
        direct_launch_match = re.search(
            r'(?:i will|i\'ll|let me|going to|need to|must)\s+(?:open|launch|start)\s+(\w+)',
            reasoning_lower
        )
        if direct_launch_match:
            app_name = direct_launch_match.group(1)
            allowed_apps = AppLauncher.get_allowed_apps()
            if app_name in allowed_apps:
                return ActionIntent(
                    action_type="launch_app",
                    confidence=0.9,
                    params={"app_name": app_name},
                    reason=f"Direct intent to launch: {app_name}"
                )
        
        # PRIORITY 3: Check typing intent - but only for ACTUAL typing actions
        # e.g., "type into notepad" should trigger type_text, not launch_app
        # But "open notepad to write" should trigger launch_app
        typing_keywords = ["type", "enter text", "input text", "typing"]
        # "write" is ambiguous - only count it if followed by quotes or specific text
        has_typing_intent = any(kw in reasoning_lower for kw in typing_keywords)
        
        # Check if "write" is for actual typing (has quoted text) vs opening app (to write later)
        if not has_typing_intent and "write" in reasoning_lower:
            # Only consider it typing if there's quoted text to type
            if cls.extract_quoted_text(reasoning):
                has_typing_intent = True
        
        if has_typing_intent:
            # First try to extract quoted text
            quoted = cls.extract_quoted_text(reasoning)
            if quoted:
                return ActionIntent(
                    action_type="type_text",
                    confidence=0.9,
                    params={"text": quoted},
                    reason="Extracted text to type from quotes"
                )
            # If no quotes but clear typing intent with a message pattern
            # Look for patterns like "type: message" or "message: 'text'"
            message_patterns = [
                r'type[:\s]+["\']([^"\']+)["\']',
                r'message[:\s]+["\']([^"\']+)["\']',
                r'text[:\s]+["\']([^"\']+)["\']',
                r'write[:\s]+["\']([^"\']+)["\']',
            ]
            for pattern in message_patterns:
                match = re.search(pattern, reasoning, re.IGNORECASE)
                if match:
                    return ActionIntent(
                        action_type="type_text",
                        confidence=0.85,
                        params={"text": match.group(1)},
                        reason="Extracted text from message pattern"
                    )
            # If still no text found but typing intent is clear, use context or generate from task
            return cls.parse_typing_intent(reasoning, context, task)
        
        # PRIORITY 4: Try to parse app launch (if not caught above)
        app_intent = cls.parse_app_launch(reasoning)
        if app_intent:
            return app_intent
        
        # Try to parse key press
        key_intent = cls.parse_key_press(reasoning)
        if key_intent:
            return key_intent
        
        # Try to parse click intent
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
