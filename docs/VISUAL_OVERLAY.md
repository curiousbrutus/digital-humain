# Visual Overlay System

## Overview

The visual overlay provides real-time feedback about agent actions, making automation transparent and easy to follow.

## Features

### Action Indicators

1. **Click Indicators**
   - Colorful crosshair and circle at click position
   - Different colors for left/right/middle clicks
   - Label showing "LEFT CLICK", "RIGHT CLICK", etc.
   - Fades out after 0.8 seconds

2. **Typing Indicators**
   - Keyboard icon at cursor position
   - Shows preview of text being typed (truncated to 20 chars)
   - Green accent color for visibility
   - Persists during typing, fades after completion

3. **Generic Action Indicators**
   - Circle marker with custom text
   - Used for hover, wait, and other actions
   - Orange color by default

4. **Region Highlighting**
   - Rectangular bounding box around UI elements
   - Dashed border for non-intrusive visibility
   - Label showing element description

5. **Status Messages**
   - Bottom-center status bar
   - Shows current task status
   - Useful for long-running operations

## Configuration

### In GUI Application

Toggle visual indicators via checkbox in "Recording & Memory" section:
- ☑ **Visual Indicators** - Enable/disable overlay

### Programmatic Usage

```python
from digital_humain.vlm.overlay import get_overlay, OverlayConfig

# Configure overlay
config = OverlayConfig(
    enabled=True,
    click_color="#4dd0ff",      # Cyan
    type_color="#50fa7b",       # Green
    hover_color="#ffb86c",      # Orange
    indicator_size=40,
    fade_duration=0.8,          # seconds
    label_bg="#282a36",
    label_fg="#f8f8f2",
    font_size=12
)

overlay = get_overlay(config)
overlay.start()

# Show indicators
overlay.show_click(100, 200, "left")
overlay.show_typing(300, 400, "Hello World")
overlay.show_action(500, 600, "Analyzing...")
overlay.show_region(100, 100, 200, 150, "Login Form")
overlay.show_status("Task in progress...")

# Stop overlay
overlay.stop()
```

### With GUIActions

```python
from digital_humain.vlm.actions import GUIActions

# Enable overlay (default)
actions = GUIActions(show_overlay=True)

# Disable overlay
actions = GUIActions(show_overlay=False)

# Actions automatically show indicators
actions.click(100, 200)           # Shows click indicator
actions.type_text("Hello World")  # Shows typing indicator
```

## Technical Details

### Overlay Window

- **Transparent**: Background is transparent, only indicators visible
- **Always on Top**: Stays above all windows
- **Non-Interactive**: Mouse events pass through
- **Full Screen**: Covers entire screen for any-position indicators
- **Thread-Safe**: Runs in separate thread, doesn't block main execution

### Performance

- Minimal overhead (~5ms per indicator)
- Automatic cleanup after fade duration
- Canvas-based rendering for efficiency
- No impact on automation accuracy

### Platform Support

- **Windows**: Full support
- **Linux**: Requires X11, may need compositor adjustments
- **macOS**: May require accessibility permissions

## Troubleshooting

### Overlay not appearing
```python
from digital_humain.vlm.overlay import get_overlay

overlay = get_overlay()
print(f"Running: {overlay.is_running}")
print(f"Enabled: {overlay.config.enabled}")
```

### Indicators not visible
- Check `overlay.config.enabled = True`
- Verify colors contrast with background
- Ensure window is not minimized

### Performance issues
- Reduce `fade_duration` (default 0.8s)
- Increase `indicator_size` for clearer visibility
- Disable overlay for performance-critical tasks

## Future Enhancements

- [ ] Path tracing for mouse movements
- [ ] Screenshot annotations
- [ ] Customizable themes (colors, sizes)
- [ ] Recording mode (save indicator overlays to video)
- [ ] Heat map of most-used screen areas
- [ ] Text-to-speech status announcements
