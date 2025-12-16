# Desktop Application Discovery

## Overview

Digital Humain automatically discovers and launches applications on your Desktop, Start Menu, and Program Files directories. This allows the agent to open your specific programs (like Bizmed, HBYS, etc.) without manual configuration.

## How It Works

### Discovery Process

The system scans multiple locations on your computer:

**Windows:**
- Desktop (`C:\Users\<username>\Desktop`)
- OneDrive Desktop (`C:\Users\<username>\OneDrive\Desktop`)
- Program Files (`C:\Program Files`)
- Program Files (x86) (`C:\Program Files (x86)`)

**Supported File Types:**
- `.exe` - Executable files
- `.lnk` - Shortcuts (Desktop shortcuts)

### Discovery Strategy

1. **Desktop Priority**: Applications on your Desktop are discovered first and take precedence
2. **Program Files**: Scans one level deep in Program Files directories
3. **Caching**: Discovered apps are cached for performance (refreshed on app restart)
4. **Base Apps**: System apps (notepad, calc, paint) are always available

### Application Matching

The launcher supports multiple matching strategies:

1. **Exact Match**: `"bizmed"` matches `bizmed.exe` or `Bizmed.lnk`
2. **Fuzzy Match**: `"biz"` can match `bizmed`, `bizicsnet`, etc.
3. **Case-Insensitive**: `"BIZMED"` matches `bizmed.lnk`

## Usage Examples

### Opening Desktop Applications

```python
from digital_humain.agents.action_parser import AppLauncher

# Launch Bizmed (from Desktop shortcut)
result = AppLauncher.launch_app("bizmed")
# Result: Opens C:\Users\<username>\Desktop\Bizmed.lnk

# Launch any discovered app
result = AppLauncher.launch_app("obsidian")
result = AppLauncher.launch_app("winrar")
```

### Listing Available Apps

```python
# Get all available apps (base + discovered)
apps = AppLauncher.get_allowed_apps()
print(f"Total apps: {len(apps)}")

# Show app names and paths
for name, path in list(apps.items())[:10]:
    print(f"{name}: {path}")
```

### Refreshing Discovery

```python
# Force refresh of discovered apps (e.g., after installing new software)
AppLauncher.refresh_discovered_apps()
```

## Natural Language Integration

When using the agent, you can request applications naturally:

```
"Open Bizmed"
"Launch HBYS program"
"Start the medical software"
"Open calculator"
```

The action parser extracts the application name and uses fuzzy matching to find the correct program.

## Security Considerations

### Safe by Default

- **Allowlist-Based**: Only discovered apps can be launched (no arbitrary commands)
- **No Shell Injection**: All paths are validated and executed safely
- **Platform-Specific**: Uses appropriate launch methods per OS

### Desktop App Trust Model

Applications on your Desktop are assumed to be:
- Installed by you or your organization
- Safe to execute
- Part of your regular workflow

### Extending Discovery

To add custom search locations, modify `discover_desktop_apps()` in [action_parser.py](digital_humain/agents/action_parser.py):

```python
search_paths = [
    Path.home() / "Desktop",
    Path.home() / "OneDrive" / "Desktop",
    Path("C:\\Program Files"),
    Path("C:\\Program Files (x86)"),
    # Add custom paths:
    Path("C:\\CustomApps"),
    Path("D:\\Medical Software"),
]
```

## Technical Details

### Implementation

**Location**: [digital_humain/agents/action_parser.py](digital_humain/agents/action_parser.py)

**Key Classes**:
- `AppLauncher`: Main application launcher with discovery
- `ActionParser`: Parses reasoning text to extract app launch intents

**Key Methods**:
- `discover_desktop_apps()`: Scans file system for applications
- `get_allowed_apps()`: Returns base + discovered apps (with caching)
- `launch_app(app_name)`: Launches app by name (exact or fuzzy match)
- `refresh_discovered_apps()`: Forces cache refresh

### Windows Shortcut Handling

`.lnk` files (shortcuts) are handled using `os.startfile()` which properly resolves the target and launches the application with the correct working directory.

### Performance

- **First Call**: ~200-500ms (scans Desktop and Program Files)
- **Subsequent Calls**: Instant (cached)
- **Cache Lifetime**: Until app restart

### Logging

Discovery process logs all found applications:

```
2025-12-16 11:16:35 | DEBUG | Discovered app: bizmed -> C:\Users\...\Desktop\Bizmed.lnk
2025-12-16 11:16:35 | DEBUG | Discovered app: obsidian -> C:\Users\...\Desktop\Obsidian.lnk
2025-12-16 11:16:35 | INFO  | Discovered 91 applications
```

Launch attempts are also logged:

```
2025-12-16 11:20:15 | INFO | Fuzzy matched 'biz' to 'bizmed'
2025-12-16 11:20:15 | INFO | Launched app: bizmed (C:\Users\...\Desktop\Bizmed.lnk)
```

## Troubleshooting

### App Not Found

If your application isn't discovered:

1. **Check Location**: Is it on Desktop or in Program Files?
2. **Check File Type**: Is it `.exe` or `.lnk`?
3. **Check Name**: What's the exact filename? (Use test script)
4. **Refresh Discovery**: Restart the app or call `refresh_discovered_apps()`

### Testing Discovery

Use the test script to see what's discovered:

```bash
python test_app_discovery.py
```

This shows:
- All discovered applications
- Search results for specific terms
- Total available apps

### App Won't Launch

If discovery works but launch fails:

1. **Check Permissions**: Can you double-click the app manually?
2. **Check Path**: Does the `.lnk` target still exist?
3. **Check Logs**: Look for error messages in the log file

## Future Enhancements

- [ ] Start Menu shortcut discovery
- [ ] Context-aware app selection (remember "HBYS" means "Bizmed")
- [ ] App window management (activate existing instead of launching new)
- [ ] User-defined aliases (`"medical" -> "bizmed"`)
- [ ] Persistent discovery cache across restarts
- [ ] GUI for managing discovered apps

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Action Parser Implementation](../digital_humain/agents/action_parser.py)
- [Agent Development Guide](../.github/copilot-instructions.md)
