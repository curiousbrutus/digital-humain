"""Test launching discovered apps."""

from digital_humain.agents.action_parser import AppLauncher
from loguru import logger
import time

logger.add("test_launch.log", rotation="1 MB")

print("=" * 60)
print("Testing App Launch with Discovery")
print("=" * 60)

# Test 1: Launch Bizmed (from Desktop)
print("\n1. Testing Bizmed launch...")
result = AppLauncher.launch_app("bizmed")
print(f"Result: {result}")

if result["success"]:
    print("✓ Bizmed launched successfully!")
    print("Note: Check if Bizmed window opened (will wait 3 seconds)")
    time.sleep(3)
else:
    print(f"✗ Failed: {result.get('error', 'Unknown error')}")

# Test 2: Fuzzy match
print("\n2. Testing fuzzy match (biz)...")
result = AppLauncher.launch_app("biz")
print(f"Result: {result}")

if result["success"]:
    print("✓ Fuzzy match worked!")
else:
    print(f"✗ Failed: {result.get('error', 'Unknown error')}")

# Test 3: System app (notepad)
print("\n3. Testing system app (notepad)...")
result = AppLauncher.launch_app("notepad")
print(f"Result: {result}")

if result["success"]:
    print("✓ Notepad launched!")
else:
    print(f"✗ Failed: {result.get('error', 'Unknown error')}")

# Test 4: Non-existent app
print("\n4. Testing non-existent app...")
result = AppLauncher.launch_app("nonexistent123")
print(f"Result: {result}")

if not result["success"]:
    print("✓ Correctly rejected non-existent app")
else:
    print("✗ Should have rejected non-existent app")

print("\n" + "=" * 60)
print("Test complete! Check test_launch.log for details.")
print("=" * 60)
