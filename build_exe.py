"""Build script for creating Digital Humain executable.

Cross-platform build script supporting Windows, Linux, and macOS.
"""

import PyInstaller.__main__
import sys
import platform
from pathlib import Path


def get_platform_info() -> dict:
    """Get platform-specific build information."""
    system = platform.system()
    
    if system == "Windows":
        return {
            "separator": ";",
            "exe_name": "DigitalHumain.exe",
            "icon_ext": ".ico",
        }
    elif system == "Darwin":  # macOS
        return {
            "separator": ":",
            "exe_name": "DigitalHumain.app",
            "icon_ext": ".icns",
        }
    else:  # Linux
        return {
            "separator": ":",
            "exe_name": "DigitalHumain",
            "icon_ext": ".png",
        }


def build():
    """Build the executable using PyInstaller."""
    
    # Get project root
    root = Path(__file__).parent
    
    # Get platform-specific settings
    plat = get_platform_info()
    sep = plat["separator"]
    exe_name = plat["exe_name"]
    
    # PyInstaller arguments
    args = [
        'gui_app.py',  # Main script
        '--name=DigitalHumain',
        '--onefile',  # Single exe file
        '--windowed',  # No console window
        '--clean',
        
        # Add data files (platform-aware separator)
        f'--add-data={root / "config" / "config.yaml"}{sep}config',
        f'--add-data={root / "digital_humain"}{sep}digital_humain',
        
        # Hidden imports
        '--hidden-import=tiktoken_ext.openai_public',
        '--hidden-import=tiktoken_ext',
        '--hidden-import=digital_humain.core',
        '--hidden-import=digital_humain.vlm',
        '--hidden-import=digital_humain.agents',
        '--hidden-import=digital_humain.tools',
        '--hidden-import=digital_humain.memory',
        '--hidden-import=digital_humain.orchestration',
        '--hidden-import=digital_humain.utils',
        
        # Platform-specific hidden imports
        '--hidden-import=pynput.keyboard._xorg' if platform.system() == "Linux" else '',
        '--hidden-import=pynput.mouse._xorg' if platform.system() == "Linux" else '',
        '--hidden-import=pynput.keyboard._win32' if platform.system() == "Windows" else '',
        '--hidden-import=pynput.mouse._win32' if platform.system() == "Windows" else '',
        '--hidden-import=pynput.keyboard._darwin' if platform.system() == "Darwin" else '',
        '--hidden-import=pynput.mouse._darwin' if platform.system() == "Darwin" else '',
        
        # Exclude unnecessary modules
        '--exclude-module=streamlit',
        '--exclude-module=matplotlib',
        '--exclude-module=IPython',
        
        # Output directory
        '--distpath=dist',
        '--workpath=build',
        '--specpath=.',
    ]
    
    # Filter out empty strings from platform-specific imports
    args = [arg for arg in args if arg]
    
    print(f"Building Digital Humain for {platform.system()}...")
    print(f"Output will be in: {root / 'dist' / exe_name}")
    
    PyInstaller.__main__.run(args)
    
    print("\n✅ Build complete!")
    print(f"Executable: {root / 'dist' / exe_name}")
    print("\nNote: Make sure to copy the following alongside the executable:")
    print("  - config/config.yaml")
    print("  - .env (if using API keys)")
    print("  - screenshots/ folder (will be created automatically)")

if __name__ == "__main__":
    build()
