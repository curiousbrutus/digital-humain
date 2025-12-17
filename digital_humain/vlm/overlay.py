"""
Visual overlay system for displaying agent actions in real-time.
Shows colorful indicators for mouse clicks, typing, and other GUI interactions.
"""

import tkinter as tk
from tkinter import Canvas
import threading
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from loguru import logger
import time


@dataclass
class OverlayConfig:
    """Configuration for visual overlay."""
    enabled: bool = True
    click_color: str = "#4dd0ff"  # Cyan for clicks
    type_color: str = "#50fa7b"   # Green for typing
    hover_color: str = "#ffb86c"  # Orange for hover
    indicator_size: int = 40
    fade_duration: float = 0.8  # seconds
    label_bg: str = "#282a36"
    label_fg: str = "#f8f8f2"
    font_size: int = 12


class ActionOverlay:
    """Transparent overlay window for visualizing agent actions."""
    
    def __init__(self, config: Optional[OverlayConfig] = None):
        self.config = config or OverlayConfig()
        self.root: Optional[tk.Tk] = None
        self.canvas: Optional[Canvas] = None
        self.is_running = False
        self._lock = threading.Lock()
        self._items: Dict[str, int] = {}  # Track canvas items for cleanup
        
    def start(self):
        """Start the overlay window in a separate thread."""
        if self.is_running:
            logger.warning("Overlay already running")
            return
        
        if not self.config.enabled:
            logger.info("Overlay disabled in config")
            return
        
        self.is_running = True
        thread = threading.Thread(target=self._run_overlay, daemon=True)
        thread.start()
        logger.info("Visual overlay started")
    
    def _run_overlay(self):
        """Run the overlay window (should be called in separate thread)."""
        try:
            self.root = tk.Tk()
            self.root.title("Digital Humain Overlay")
            
            # Make window transparent and always on top
            self.root.attributes('-alpha', 0.7)
            self.root.attributes('-topmost', True)
            self.root.overrideredirect(True)  # No window decorations
            
            # Full screen
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
            self.root.geometry(f"{width}x{height}+0+0")
            
            # Transparent background
            self.root.configure(bg='black')
            self.root.attributes('-transparentcolor', 'black')
            
            # Canvas for drawing
            self.canvas = Canvas(
                self.root,
                width=width,
                height=height,
                bg='black',
                highlightthickness=0
            )
            self.canvas.pack()
            
            # Allow mouse events to pass through
            self.root.wm_attributes('-transparentcolor', 'black')
            
            logger.info(f"Overlay window created: {width}x{height}")
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Error in overlay window: {e}")
        finally:
            self.is_running = False
    
    def stop(self):
        """Stop the overlay window."""
        if not self.is_running or not self.root:
            return
        
        try:
            self.root.quit()
            self.root.destroy()
            logger.info("Visual overlay stopped")
        except Exception as e:
            logger.error(f"Error stopping overlay: {e}")
        finally:
            self.is_running = False
            self.root = None
            self.canvas = None
    
    def show_click(self, x: int, y: int, button: str = "left"):
        """Show a click indicator at the given position."""
        if not self.is_running or not self.canvas:
            return
        
        color = self.config.click_color
        size = self.config.indicator_size
        
        def draw():
            try:
                # Draw pulsing circle
                oval_id = self.canvas.create_oval(
                    x - size//2, y - size//2,
                    x + size//2, y + size//2,
                    outline=color,
                    width=3,
                    fill=""
                )
                
                # Draw crosshair
                line1 = self.canvas.create_line(
                    x - size//3, y,
                    x + size//3, y,
                    fill=color,
                    width=2
                )
                line2 = self.canvas.create_line(
                    x, y - size//3,
                    x, y + size//3,
                    fill=color,
                    width=2
                )
                
                # Label
                label = self.canvas.create_text(
                    x, y + size,
                    text=f"{button.upper()} CLICK",
                    fill=self.config.label_fg,
                    font=("Arial", self.config.font_size, "bold")
                )
                label_bg = self.canvas.create_rectangle(
                    self.canvas.bbox(label),
                    fill=self.config.label_bg,
                    outline=color
                )
                self.canvas.tag_lower(label_bg, label)
                
                # Fade out after duration
                self.root.after(
                    int(self.config.fade_duration * 1000),
                    lambda: self._cleanup_items([oval_id, line1, line2, label, label_bg])
                )
            except Exception as e:
                logger.error(f"Error drawing click indicator: {e}")
        
        if self.root:
            self.root.after(0, draw)
    
    def show_typing(self, x: int, y: int, text: str):
        """Show a typing indicator at the cursor position."""
        if not self.is_running or not self.canvas:
            return
        
        color = self.config.type_color
        
        def draw():
            try:
                # Keyboard icon (simplified)
                rect = self.canvas.create_rectangle(
                    x - 30, y - 40,
                    x + 30, y - 10,
                    outline=color,
                    width=2,
                    fill=self.config.label_bg
                )
                
                # Blinking cursor
                cursor = self.canvas.create_rectangle(
                    x - 5, y - 35,
                    x + 5, y - 15,
                    fill=color,
                    outline=""
                )
                
                # Text preview (truncated)
                preview = text[:20] + "..." if len(text) > 20 else text
                label = self.canvas.create_text(
                    x, y + 10,
                    text=f'Typing: "{preview}"',
                    fill=self.config.label_fg,
                    font=("Arial", self.config.font_size)
                )
                label_bg = self.canvas.create_rectangle(
                    self.canvas.bbox(label),
                    fill=self.config.label_bg,
                    outline=color
                )
                self.canvas.tag_lower(label_bg, label)
                
                # Fade out
                self.root.after(
                    int(self.config.fade_duration * 1000),
                    lambda: self._cleanup_items([rect, cursor, label, label_bg])
                )
            except Exception as e:
                logger.error(f"Error drawing typing indicator: {e}")
        
        if self.root:
            self.root.after(0, draw)
    
    def show_action(self, x: int, y: int, action: str, color: Optional[str] = None):
        """Show a generic action indicator with custom text."""
        if not self.is_running or not self.canvas:
            return
        
        color = color or self.config.hover_color
        
        def draw():
            try:
                # Circle indicator
                circle = self.canvas.create_oval(
                    x - 25, y - 25,
                    x + 25, y + 25,
                    outline=color,
                    width=2,
                    fill=""
                )
                
                # Action label
                label = self.canvas.create_text(
                    x, y + 40,
                    text=action,
                    fill=self.config.label_fg,
                    font=("Arial", self.config.font_size, "bold")
                )
                label_bg = self.canvas.create_rectangle(
                    self.canvas.bbox(label),
                    fill=self.config.label_bg,
                    outline=color
                )
                self.canvas.tag_lower(label_bg, label)
                
                # Fade out
                self.root.after(
                    int(self.config.fade_duration * 1000),
                    lambda: self._cleanup_items([circle, label, label_bg])
                )
            except Exception as e:
                logger.error(f"Error drawing action indicator: {e}")
        
        if self.root:
            self.root.after(0, draw)
    
    def show_region(self, x: int, y: int, width: int, height: int, label: str):
        """Highlight a rectangular region with a label."""
        if not self.is_running or not self.canvas:
            return
        
        color = self.config.click_color
        
        def draw():
            try:
                # Bounding box
                rect = self.canvas.create_rectangle(
                    x, y, x + width, y + height,
                    outline=color,
                    width=3,
                    dash=(5, 3)
                )
                
                # Label at top
                text = self.canvas.create_text(
                    x + width // 2, y - 10,
                    text=label,
                    fill=self.config.label_fg,
                    font=("Arial", self.config.font_size, "bold")
                )
                text_bg = self.canvas.create_rectangle(
                    self.canvas.bbox(text),
                    fill=self.config.label_bg,
                    outline=color
                )
                self.canvas.tag_lower(text_bg, text)
                
                # Fade out
                self.root.after(
                    int(self.config.fade_duration * 1500),  # Longer for regions
                    lambda: self._cleanup_items([rect, text, text_bg])
                )
            except Exception as e:
                logger.error(f"Error drawing region indicator: {e}")
        
        if self.root:
            self.root.after(0, draw)
    
    def show_status(self, message: str, duration: float = 2.0):
        """Show a status message at the bottom of the screen."""
        if not self.is_running or not self.canvas:
            return
        
        def draw():
            try:
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Status bar at bottom
                y = screen_height - 60
                
                label = self.canvas.create_text(
                    screen_width // 2, y,
                    text=message,
                    fill=self.config.label_fg,
                    font=("Arial", self.config.font_size + 2, "bold")
                )
                
                bbox = self.canvas.bbox(label)
                padding = 10
                bg = self.canvas.create_rectangle(
                    bbox[0] - padding, bbox[1] - padding,
                    bbox[2] + padding, bbox[3] + padding,
                    fill=self.config.label_bg,
                    outline=self.config.click_color,
                    width=2
                )
                self.canvas.tag_lower(bg, label)
                
                # Fade out
                self.root.after(
                    int(duration * 1000),
                    lambda: self._cleanup_items([label, bg])
                )
            except Exception as e:
                logger.error(f"Error drawing status: {e}")
        
        if self.root:
            self.root.after(0, draw)
    
    def _cleanup_items(self, items: list):
        """Remove canvas items."""
        if not self.canvas:
            return
        
        try:
            for item in items:
                self.canvas.delete(item)
        except Exception as e:
            logger.error(f"Error cleaning up items: {e}")
    
    def clear(self):
        """Clear all indicators from the canvas."""
        if not self.canvas:
            return
        
        try:
            self.canvas.delete("all")
        except Exception as e:
            logger.error(f"Error clearing canvas: {e}")


# Global singleton instance
_overlay_instance: Optional[ActionOverlay] = None


def get_overlay(config: Optional[OverlayConfig] = None) -> ActionOverlay:
    """Get the global overlay instance (singleton pattern)."""
    global _overlay_instance
    
    if _overlay_instance is None:
        _overlay_instance = ActionOverlay(config)
    
    return _overlay_instance


def enable_overlay():
    """Enable the visual overlay."""
    overlay = get_overlay()
    overlay.config.enabled = True
    if not overlay.is_running:
        overlay.start()


def disable_overlay():
    """Disable the visual overlay."""
    overlay = get_overlay()
    overlay.config.enabled = False
    overlay.stop()
