"""Test script for desktop app discovery."""

from digital_humain.agents.action_parser import AppLauncher
from loguru import logger

# Configure logger
logger.add("test_discovery.log", rotation="1 MB")

print("=" * 60)
print("Testing Desktop App Discovery")
print("=" * 60)

# Discover apps
print("\n1. Discovering desktop applications...")
discovered = AppLauncher.discover_desktop_apps()

print(f"\nFound {len(discovered)} applications:")
print("-" * 60)

# Show first 30 discovered apps
for i, (name, path) in enumerate(list(discovered.items())[:30], 1):
    print(f"{i:2}. {name:30} -> {path}")

if len(discovered) > 30:
    print(f"... and {len(discovered) - 30} more apps")

# Check for specific apps
print("\n" + "=" * 60)
print("Looking for specific apps...")
print("=" * 60)

search_terms = ["bizmed", "hbys", "notepad", "chrome", "excel", "word"]
for term in search_terms:
    matches = [name for name in discovered.keys() if term.lower() in name.lower()]
    if matches:
        print(f"\n✓ Found '{term}': {matches}")
    else:
        print(f"\n✗ '{term}' not found")

# Test get_allowed_apps (includes base + discovered)
print("\n" + "=" * 60)
print("Testing get_allowed_apps() (base + discovered)...")
print("=" * 60)

all_apps = AppLauncher.get_allowed_apps()
print(f"\nTotal available apps: {len(all_apps)}")

# Show base system apps
base_apps = ["notepad", "calc", "paint"]
print("\nBase system apps:")
for app in base_apps:
    if app in all_apps:
        print(f"  ✓ {app}: {all_apps[app]}")

print("\n" + "=" * 60)
print("Test complete! Check test_discovery.log for detailed logs.")
print("=" * 60)
