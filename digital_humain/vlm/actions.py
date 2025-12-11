"""GUI action execution for desktop automation."""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import time
import pyautogui
from loguru import logger


class ActionType(str, Enum):
    """Types of GUI actions."""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    HOTKEY = "hotkey"
    MOVE_MOUSE = "move_mouse"
    SCROLL = "scroll"
    DRAG = "drag"
    SCREENSHOT = "screenshot"
    WAIT = "wait"


class GUIActions:
    """
    Execute GUI actions for desktop automation.
    
    Provides methods for interacting with desktop applications.
    """
    
    def __init__(self, pause: float = 0.5, safe_mode: bool = True):
        """
        Initialize GUI actions executor.
        
        Args:
            pause: Pause duration between actions (seconds)
            safe_mode: Enable fail-safe (move mouse to corner to abort)
        """
        pyautogui.PAUSE = pause
        pyautogui.FAILSAFE = safe_mode
        self.action_history: List[Dict[str, Any]] = []
        logger.info(f"Initialized GUIActions (pause={pause}s, safe_mode={safe_mode})")
    
    def _log_action(self, action_type: ActionType, params: Dict[str, Any]) -> None:
        """Log executed action."""
        self.action_history.append({
            "type": action_type.value,
            "params": params,
            "timestamp": time.time()
        })
        logger.debug(f"Action executed: {action_type.value} - {params}")
    
    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        clicks: int = 1,
        button: str = "left"
    ) -> Dict[str, Any]:
        """
        Click at specified position or current position.
        
        Args:
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            clicks: Number of clicks
            button: Mouse button ('left', 'right', 'middle')
            
        Returns:
            Action result dictionary
        """
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
            else:
                pyautogui.click(clicks=clicks, button=button)
            
            self._log_action(ActionType.CLICK, {
                "x": x, "y": y, "clicks": clicks, "button": button
            })
            
            return {
                "action": ActionType.CLICK.value,
                "success": True,
                "position": (x, y) if x and y else pyautogui.position()
            }
        
        except Exception as e:
            logger.error(f"Click action failed: {e}")
            return {
                "action": ActionType.CLICK.value,
                "success": False,
                "error": str(e)
            }
    
    def double_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Double-click at specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Action result dictionary
        """
        return self.click(x, y, clicks=2)
    
    def right_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Right-click at specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Action result dictionary
        """
        return self.click(x, y, button="right")
    
    def type_text(
        self,
        text: str,
        interval: float = 0.0
    ) -> Dict[str, Any]:
        """
        Type text at current cursor position.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes (seconds)
            
        Returns:
            Action result dictionary
        """
        try:
            pyautogui.write(text, interval=interval)
            
            self._log_action(ActionType.TYPE_TEXT, {
                "text": text, "interval": interval
            })
            
            return {
                "action": ActionType.TYPE_TEXT.value,
                "success": True,
                "text": text
            }
        
        except Exception as e:
            logger.error(f"Type text action failed: {e}")
            return {
                "action": ActionType.TYPE_TEXT.value,
                "success": False,
                "error": str(e)
            }
    
    def press_key(self, key: str, presses: int = 1) -> Dict[str, Any]:
        """
        Press a keyboard key.
        
        Args:
            key: Key name (e.g., 'enter', 'tab', 'esc')
            presses: Number of times to press
            
        Returns:
            Action result dictionary
        """
        try:
            pyautogui.press(key, presses=presses)
            
            self._log_action(ActionType.PRESS_KEY, {
                "key": key, "presses": presses
            })
            
            return {
                "action": ActionType.PRESS_KEY.value,
                "success": True,
                "key": key
            }
        
        except Exception as e:
            logger.error(f"Press key action failed: {e}")
            return {
                "action": ActionType.PRESS_KEY.value,
                "success": False,
                "error": str(e)
            }
    
    def hotkey(self, *keys: str) -> Dict[str, Any]:
        """
        Press a combination of keys (hotkey).
        
        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c')
            
        Returns:
            Action result dictionary
        """
        try:
            pyautogui.hotkey(*keys)
            
            self._log_action(ActionType.HOTKEY, {"keys": keys})
            
            return {
                "action": ActionType.HOTKEY.value,
                "success": True,
                "keys": keys
            }
        
        except Exception as e:
            logger.error(f"Hotkey action failed: {e}")
            return {
                "action": ActionType.HOTKEY.value,
                "success": False,
                "error": str(e)
            }
    
    def move_mouse(
        self,
        x: int,
        y: int,
        duration: float = 0.5
    ) -> Dict[str, Any]:
        """
        Move mouse to specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Movement duration (seconds)
            
        Returns:
            Action result dictionary
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            
            self._log_action(ActionType.MOVE_MOUSE, {
                "x": x, "y": y, "duration": duration
            })
            
            return {
                "action": ActionType.MOVE_MOUSE.value,
                "success": True,
                "position": (x, y)
            }
        
        except Exception as e:
            logger.error(f"Move mouse action failed: {e}")
            return {
                "action": ActionType.MOVE_MOUSE.value,
                "success": False,
                "error": str(e)
            }
    
    def scroll(
        self,
        clicks: int,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scroll up or down.
        
        Args:
            clicks: Number of clicks (positive=up, negative=down)
            x: X coordinate for scroll position
            y: Y coordinate for scroll position
            
        Returns:
            Action result dictionary
        """
        try:
            if x is not None and y is not None:
                pyautogui.scroll(clicks, x, y)
            else:
                pyautogui.scroll(clicks)
            
            self._log_action(ActionType.SCROLL, {
                "clicks": clicks, "x": x, "y": y
            })
            
            return {
                "action": ActionType.SCROLL.value,
                "success": True,
                "clicks": clicks
            }
        
        except Exception as e:
            logger.error(f"Scroll action failed: {e}")
            return {
                "action": ActionType.SCROLL.value,
                "success": False,
                "error": str(e)
            }
    
    def drag(
        self,
        x: int,
        y: int,
        duration: float = 0.5,
        button: str = "left"
    ) -> Dict[str, Any]:
        """
        Drag mouse to specified position.
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Drag duration (seconds)
            button: Mouse button to use
            
        Returns:
            Action result dictionary
        """
        try:
            pyautogui.drag(x, y, duration=duration, button=button)
            
            self._log_action(ActionType.DRAG, {
                "x": x, "y": y, "duration": duration, "button": button
            })
            
            return {
                "action": ActionType.DRAG.value,
                "success": True,
                "position": (x, y)
            }
        
        except Exception as e:
            logger.error(f"Drag action failed: {e}")
            return {
                "action": ActionType.DRAG.value,
                "success": False,
                "error": str(e)
            }
    
    def wait(self, seconds: float) -> Dict[str, Any]:
        """
        Wait for specified duration.
        
        Args:
            seconds: Duration to wait
            
        Returns:
            Action result dictionary
        """
        try:
            time.sleep(seconds)
            
            self._log_action(ActionType.WAIT, {"seconds": seconds})
            
            return {
                "action": ActionType.WAIT.value,
                "success": True,
                "duration": seconds
            }
        
        except Exception as e:
            logger.error(f"Wait action failed: {e}")
            return {
                "action": ActionType.WAIT.value,
                "success": False,
                "error": str(e)
            }
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """
        Get current mouse position.
        
        Returns:
            (x, y) tuple
        """
        pos = pyautogui.position()
        return (pos.x, pos.y)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get screen dimensions.
        
        Returns:
            (width, height) tuple
        """
        size = pyautogui.size()
        return (size.width, size.height)
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """
        Get history of executed actions.
        
        Returns:
            List of action dictionaries
        """
        return self.action_history.copy()
    
    def clear_history(self) -> None:
        """Clear action history."""
        self.action_history.clear()
        logger.info("Action history cleared")
