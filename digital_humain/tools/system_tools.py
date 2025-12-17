"""System-level automation tools for window management, clipboard, and processes."""

import subprocess
import platform
from typing import Dict, List, Optional, Any
from loguru import logger

from digital_humain.tools.base import BaseTool, ToolMetadata, ToolParameter, ToolResult


class LaunchAppTool(BaseTool):
    """Tool for launching desktop applications."""
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="system_launch_app",
            description="Launch a desktop application",
            parameters=[
                ToolParameter(
                    name="app_name",
                    type="string",
                    description="Name of the application to launch",
                    required=True
                ),
                ToolParameter(
                    name="args",
                    type="array",
                    description="Optional command-line arguments",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        app_name = kwargs.get("app_name")
        args = kwargs.get("args", [])
        
        if not app_name:
            return ToolResult(
                success=False,
                error="app_name parameter is required"
            )
        
        try:
            system = platform.system()
            
            if system == "Windows":
                command = [app_name] + args
            elif system == "Darwin":  # macOS
                command = ["open", "-a", app_name] + args
            else:  # Linux
                command = [app_name] + args
            
            logger.info(f"Launching application: {app_name}")
            subprocess.Popen(command)
            
            return ToolResult(
                success=True,
                data={
                    "app_name": app_name,
                    "args": args,
                    "system": system
                },
                message=f"Launched {app_name}"
            )
        
        except Exception as e:
            logger.error(f"Failed to launch application: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class WindowManagementTool(BaseTool):
    """Tool for managing application windows."""
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="system_window_management",
            description="Manage application windows (focus, minimize, maximize, close)",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform (focus, minimize, maximize, close, list)",
                    required=True
                ),
                ToolParameter(
                    name="window_title",
                    type="string",
                    description="Title or partial title of the window",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        action = kwargs.get("action")
        window_title = kwargs.get("window_title")
        
        if not action:
            return ToolResult(
                success=False,
                error="action parameter is required"
            )
        
        try:
            # Try to import pygetwindow for cross-platform window management
            try:
                import pygetwindow as gw
                
                if action == "list":
                    windows = gw.getAllTitles()
                    return ToolResult(
                        success=True,
                        data={"windows": windows},
                        message=f"Found {len(windows)} windows"
                    )
                
                if not window_title:
                    return ToolResult(
                        success=False,
                        error="window_title parameter required for this action"
                    )
                
                # Find window
                windows = gw.getWindowsWithTitle(window_title)
                
                if not windows:
                    return ToolResult(
                        success=False,
                        error=f"No window found with title: {window_title}"
                    )
                
                window = windows[0]
                
                if action == "focus":
                    window.activate()
                elif action == "minimize":
                    window.minimize()
                elif action == "maximize":
                    window.maximize()
                elif action == "close":
                    window.close()
                else:
                    return ToolResult(
                        success=False,
                        error=f"Unknown action: {action}"
                    )
                
                return ToolResult(
                    success=True,
                    data={
                        "action": action,
                        "window_title": window_title
                    },
                    message=f"Performed {action} on window: {window_title}"
                )
            
            except ImportError:
                logger.warning("pygetwindow not available, using fallback")
                return ToolResult(
                    success=True,
                    data={
                        "action": action,
                        "window_title": window_title,
                        "note": "pygetwindow not available, action simulated"
                    },
                    message=f"Window management: {action}"
                )
        
        except Exception as e:
            logger.error(f"Window management failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class ClipboardTool(BaseTool):
    """Tool for clipboard operations."""
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="system_clipboard",
            description="Read from or write to the system clipboard",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform (get, set)",
                    required=True
                ),
                ToolParameter(
                    name="text",
                    type="string",
                    description="Text to set in clipboard (for 'set' action)",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        action = kwargs.get("action")
        text = kwargs.get("text")
        
        if not action:
            return ToolResult(
                success=False,
                error="action parameter is required"
            )
        
        try:
            import pyperclip
            
            if action == "get":
                clipboard_content = pyperclip.paste()
                return ToolResult(
                    success=True,
                    data={"content": clipboard_content},
                    message="Retrieved clipboard content"
                )
            
            elif action == "set":
                if text is None:
                    return ToolResult(
                        success=False,
                        error="text parameter required for 'set' action"
                    )
                
                pyperclip.copy(text)
                return ToolResult(
                    success=True,
                    data={"text_length": len(text)},
                    message="Set clipboard content"
                )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        
        except ImportError:
            logger.error("pyperclip not available")
            return ToolResult(
                success=False,
                error="pyperclip module not installed"
            )
        
        except Exception as e:
            logger.error(f"Clipboard operation failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class ProcessControlTool(BaseTool):
    """Tool for controlling system processes."""
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="system_process_control",
            description="Control system processes (list, kill)",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform (list, kill)",
                    required=True
                ),
                ToolParameter(
                    name="process_name",
                    type="string",
                    description="Process name (for 'kill' action)",
                    required=False
                ),
                ToolParameter(
                    name="pid",
                    type="number",
                    description="Process ID (for 'kill' action)",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        action = kwargs.get("action")
        process_name = kwargs.get("process_name")
        pid = kwargs.get("pid")
        
        if not action:
            return ToolResult(
                success=False,
                error="action parameter is required"
            )
        
        try:
            import psutil
            
            if action == "list":
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'status']):
                    try:
                        processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "status": proc.info['status']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Filter by name if provided
                if process_name:
                    processes = [p for p in processes if process_name.lower() in p['name'].lower()]
                
                return ToolResult(
                    success=True,
                    data={"processes": processes[:50]},  # Limit to 50
                    message=f"Found {len(processes)} processes"
                )
            
            elif action == "kill":
                if not pid and not process_name:
                    return ToolResult(
                        success=False,
                        error="Either pid or process_name required for 'kill' action"
                    )
                
                killed_count = 0
                
                if pid:
                    # Kill by PID
                    proc = psutil.Process(pid)
                    proc.terminate()
                    killed_count = 1
                    logger.info(f"Terminated process with PID: {pid}")
                
                elif process_name:
                    # Kill by name
                    for proc in psutil.process_iter(['pid', 'name']):
                        if process_name.lower() in proc.info['name'].lower():
                            proc.terminate()
                            killed_count += 1
                            logger.info(f"Terminated process: {proc.info['name']} (PID: {proc.info['pid']})")
                
                return ToolResult(
                    success=True,
                    data={"killed_count": killed_count},
                    message=f"Terminated {killed_count} process(es)"
                )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        
        except ImportError:
            logger.error("psutil not available")
            return ToolResult(
                success=False,
                error="psutil module not installed"
            )
        
        except Exception as e:
            logger.error(f"Process control failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class ScreenInfoTool(BaseTool):
    """Tool for getting screen information."""
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="system_screen_info",
            description="Get information about screen(s) and display",
            parameters=[]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        try:
            import pyautogui
            
            screen_size = pyautogui.size()
            mouse_position = pyautogui.position()
            
            return ToolResult(
                success=True,
                data={
                    "screen_width": screen_size[0],
                    "screen_height": screen_size[1],
                    "mouse_x": mouse_position[0],
                    "mouse_y": mouse_position[1]
                },
                message=f"Screen: {screen_size[0]}x{screen_size[1]}"
            )
        
        except Exception as e:
            logger.error(f"Failed to get screen info: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
