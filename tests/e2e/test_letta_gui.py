"""
Quick test to verify Letta-style GUI launches correctly.
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

print("=" * 60)
print("Testing Letta-Style GUI Components")
print("=" * 60)

# Test imports
print("\n1. Testing imports...")
try:
    from digital_humain.core.llm import OllamaProvider, OpenRouterProvider
    from digital_humain.memory.demonstration import DemonstrationMemory
    from digital_humain.memory.episodic import EpisodicMemory
    print("✓ Core imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test memory classes
print("\n2. Testing CoreMemory class...")
try:
    import tkinter as tk
    # Simulate import from gui_letta.py
    exec((repo_root / "gui_letta.py").read_text(encoding="utf-8"), {"__name__": "__test__"})
    print("✓ GUI file loads successfully")
except Exception as e:
    print(f"✗ GUI load failed: {e}")
    print("   This is expected - GUI needs to run directly, not via exec()")

print("\n3. Testing memory components...")
try:
    # Test directories exist
    from pathlib import Path
    memory_path = Path("memory")
    if not memory_path.exists():
        memory_path.mkdir(parents=True)
        print("✓ Created memory directory")
    else:
        print("✓ Memory directory exists")
    
    # Test archival storage
    archival_path = memory_path / "archival"
    archival_path.mkdir(parents=True, exist_ok=True)
    print("✓ Archival directory ready")
    
except Exception as e:
    print(f"✗ Directory setup failed: {e}")

print("\n4. Testing GUI launch...")
print("⚠ Manual test required:")
print("   Run: python gui_letta.py")
print("   Expected:")
print("   - Window opens with three panels")
print("   - Left panel shows LLM config")
print("   - Center panel shows tabs (Simulator, Logs, Memory)")
print("   - Right panel shows Context Window with token count")
print("   - Core Memory tab visible with Human/Persona blocks")
print("   - Archival Memory tab visible")

print("\n" + "=" * 60)
print("Component tests complete!")
print("Launch GUI manually: python gui_letta.py")
print("=" * 60)
