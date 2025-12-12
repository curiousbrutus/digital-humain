"""Demonstration memory for recording and replaying user actions."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger

# Optional GUI dependencies - allow import without display
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except (ImportError, KeyError):
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not available or no display - recording/replay disabled")

try:
    from pynput import mouse, keyboard
    PYNPUT_AVAILABLE = True
except (ImportError, KeyError):
    PYNPUT_AVAILABLE = False
    logger.warning("pynput not available - recording disabled")


class RecordedAction(BaseModel):
    """A single recorded user action."""
    
    timestamp: float
    action_type: str  # 'mouse_click', 'mouse_move', 'key_press', 'key_release', 'text_type'
    params: Dict[str, Any]
    window_title: Optional[str] = None
    screen_size: Optional[tuple] = None


class ActionRecorder:
    """Records user mouse and keyboard actions with context."""
    
    def __init__(self):
        """Initialize the action recorder."""
        self.is_recording = False
        self.actions: List[RecordedAction] = []
        self.start_time: Optional[float] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        logger.info("ActionRecorder initialized")
    
    def start_recording(self) -> None:
        """Start recording user actions."""
        if not PYNPUT_AVAILABLE:
            logger.error("Cannot start recording - pynput not available")
            return
        
        if self.is_recording:
            logger.warning("Already recording")
            return
        
        self.is_recording = True
        self.actions = []
        self.start_time = time.time()
        
        # Get current window info (platform-specific, basic implementation)
        try:
            import pygetwindow as gw
            active_window = gw.getActiveWindow()
            self.current_window = active_window.title if active_window else "Unknown"
        except (ImportError, AttributeError, Exception) as e:
            logger.debug(f"Could not get active window: {e}")
            self.current_window = "Unknown"
        
        # Start listeners
        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        self._mouse_listener.start()
        self._keyboard_listener.start()
        
        logger.info("Recording started")
    
    def stop_recording(self) -> List[RecordedAction]:
        """Stop recording and return recorded actions."""
        if not self.is_recording:
            logger.warning("Not currently recording")
            return []
        
        self.is_recording = False
        
        # Stop listeners
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        
        logger.info(f"Recording stopped. Captured {len(self.actions)} actions")
        return self.actions.copy()
    
    def _on_mouse_click(self, x: int, y: int, button, pressed: bool) -> None:
        """Handle mouse click events."""
        if not self.is_recording:
            return
        
        action = RecordedAction(
            timestamp=time.time() - self.start_time,
            action_type='mouse_click',
            params={
                'x': x,
                'y': y,
                'button': str(button),
                'pressed': pressed
            },
            window_title=self.current_window,
            screen_size=pyautogui.size() if PYAUTOGUI_AVAILABLE else None
        )
        self.actions.append(action)
    
    def _on_mouse_move(self, x: int, y: int) -> None:
        """Handle mouse move events (sampled to avoid too many events)."""
        if not self.is_recording:
            return
        
        # Sample move events (only record every 10th move to reduce noise)
        if len(self.actions) % 10 == 0:
            action = RecordedAction(
                timestamp=time.time() - self.start_time,
                action_type='mouse_move',
                params={'x': x, 'y': y},
                window_title=self.current_window,
                screen_size=pyautogui.size() if PYAUTOGUI_AVAILABLE else None
            )
            self.actions.append(action)
    
    def _on_key_press(self, key) -> None:
        """Handle key press events."""
        if not self.is_recording:
            return
        
        try:
            key_str = key.char if hasattr(key, 'char') else str(key)
        except:
            key_str = str(key)
        
        action = RecordedAction(
            timestamp=time.time() - self.start_time,
            action_type='key_press',
            params={'key': key_str},
            window_title=self.current_window,
            screen_size=pyautogui.size() if PYAUTOGUI_AVAILABLE else None
        )
        self.actions.append(action)
    
    def _on_key_release(self, key) -> None:
        """Handle key release events."""
        if not self.is_recording:
            return
        
        try:
            key_str = key.char if hasattr(key, 'char') else str(key)
        except:
            key_str = str(key)
        
        action = RecordedAction(
            timestamp=time.time() - self.start_time,
            action_type='key_release',
            params={'key': key_str},
            window_title=self.current_window,
            screen_size=pyautogui.size() if PYAUTOGUI_AVAILABLE else None
        )
        self.actions.append(action)


class DemonstrationMemory:
    """Manages demonstration recordings for learning from user."""
    
    def __init__(self, storage_path: str = "./demonstrations"):
        """
        Initialize demonstration memory.
        
        Args:
            storage_path: Directory to store demonstration recordings
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.recorder = ActionRecorder()
        logger.info(f"DemonstrationMemory initialized at {self.storage_path}")
    
    def start_recording(self) -> None:
        """Start recording a new demonstration."""
        self.recorder.start_recording()
    
    def stop_recording(self) -> List[RecordedAction]:
        """Stop recording and return actions."""
        return self.recorder.stop_recording()
    
    def save_demonstration(self, name: str, actions: List[RecordedAction], metadata: Optional[Dict] = None) -> None:
        """
        Save a demonstration recording.
        
        Args:
            name: Name for the demonstration
            actions: List of recorded actions
            metadata: Optional metadata dictionary
        """
        demo_data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "actions": [action.model_dump() for action in actions],
            "total_duration": actions[-1].timestamp if actions else 0,
            "action_count": len(actions)
        }
        
        filepath = self.storage_path / f"{name}.json"
        with open(filepath, 'w') as f:
            json.dump(demo_data, f, indent=2)
        
        logger.info(f"Demonstration '{name}' saved with {len(actions)} actions")
    
    def load_demonstration(self, name: str) -> Optional[Dict]:
        """
        Load a demonstration recording.
        
        Args:
            name: Name of the demonstration
            
        Returns:
            Demonstration data or None if not found
        """
        filepath = self.storage_path / f"{name}.json"
        if not filepath.exists():
            logger.warning(f"Demonstration '{name}' not found")
            return None
        
        with open(filepath, 'r') as f:
            demo_data = json.load(f)
        
        # Convert actions back to RecordedAction objects
        demo_data['actions'] = [RecordedAction(**action) for action in demo_data['actions']]
        
        logger.info(f"Demonstration '{name}' loaded with {len(demo_data['actions'])} actions")
        return demo_data
    
    def list_demonstrations(self) -> List[Dict[str, Any]]:
        """
        List all available demonstrations.
        
        Returns:
            List of demonstration metadata
        """
        demos = []
        for filepath in self.storage_path.glob("*.json"):
            with open(filepath, 'r') as f:
                demo_data = json.load(f)
                demos.append({
                    "name": demo_data["name"],
                    "created_at": demo_data["created_at"],
                    "action_count": demo_data["action_count"],
                    "duration": demo_data["total_duration"]
                })
        
        return sorted(demos, key=lambda x: x["created_at"], reverse=True)
    
    def delete_demonstration(self, name: str) -> bool:
        """
        Delete a demonstration recording.
        
        Args:
            name: Name of the demonstration
            
        Returns:
            True if deleted, False if not found
        """
        filepath = self.storage_path / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            logger.info(f"Demonstration '{name}' deleted")
            return True
        
        logger.warning(f"Demonstration '{name}' not found")
        return False
    
    def replay_demonstration(
        self,
        name: str,
        speed: float = 1.0,
        dry_run: bool = False,
        safety_pause: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Replay a demonstration.
        
        Args:
            name: Name of the demonstration to replay
            speed: Playback speed multiplier (1.0 = normal)
            dry_run: If True, just list actions without executing
            safety_pause: If True, pause before starting replay
            
        Returns:
            List of execution results
        """
        demo_data = self.load_demonstration(name)
        if not demo_data:
            return []
        
        actions = demo_data['actions']
        
        if dry_run:
            logger.info(f"DRY RUN: Would replay {len(actions)} actions")
            return [{"action": action.action_type, "params": action.params, "dry_run": True} for action in actions]
        
        if safety_pause:
            logger.warning("Starting replay in 3 seconds... Move mouse to corner to abort")
            time.sleep(3)
        
        results = []
        last_timestamp = 0
        
        for action in actions:
            # Calculate delay based on speed
            delay = (action.timestamp - last_timestamp) / speed
            if delay > 0:
                time.sleep(delay)
            last_timestamp = action.timestamp
            
            # Execute action
            result = self._execute_action(action)
            results.append(result)
        
        logger.info(f"Replay completed: {len(results)} actions executed")
        return results
    
    def _execute_action(self, action: RecordedAction) -> Dict[str, Any]:
        """
        Execute a recorded action.
        
        Args:
            action: RecordedAction to execute
            
        Returns:
            Execution result dictionary
        """
        if not PYAUTOGUI_AVAILABLE:
            return {
                "action": action.action_type,
                "success": False,
                "error": "pyautogui not available"
            }
        
        try:
            if action.action_type == 'mouse_click':
                params = action.params
                if params['pressed']:
                    pyautogui.click(params['x'], params['y'], button=params['button'])
                
                return {
                    "action": action.action_type,
                    "success": True,
                    "params": params
                }
            
            elif action.action_type == 'mouse_move':
                params = action.params
                pyautogui.moveTo(params['x'], params['y'], duration=0.1)
                
                return {
                    "action": action.action_type,
                    "success": True,
                    "params": params
                }
            
            elif action.action_type == 'key_press':
                # Map pynput keys to pyautogui keys
                key_mapping = {
                    'Key.enter': 'enter',
                    'Key.tab': 'tab',
                    'Key.space': 'space',
                    'Key.backspace': 'backspace',
                    'Key.delete': 'delete',
                    'Key.esc': 'esc',
                    'Key.shift': 'shift',
                    'Key.ctrl': 'ctrl',
                    'Key.alt': 'alt',
                    'Key.up': 'up',
                    'Key.down': 'down',
                    'Key.left': 'left',
                    'Key.right': 'right',
                    'Key.home': 'home',
                    'Key.end': 'end',
                    'Key.page_up': 'pageup',
                    'Key.page_down': 'pagedown',
                }
                
                key = action.params['key']
                # Use mapping if available, otherwise try to strip Key. prefix
                if key in key_mapping:
                    key = key_mapping[key]
                elif 'Key.' in key:
                    key = key.replace('Key.', '').lower()
                
                pyautogui.press(key)
                
                return {
                    "action": action.action_type,
                    "success": True,
                    "params": action.params
                }
            
            else:
                return {
                    "action": action.action_type,
                    "success": False,
                    "error": "Unknown action type"
                }
        
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                "action": action.action_type,
                "success": False,
                "error": str(e)
            }
