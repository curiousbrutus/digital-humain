"""Build script for creating Digital Humain executable."""

import PyInstaller.__main__
import sys
from pathlib import Path

def build():
    """Build the executable using PyInstaller."""
    
    # Get project root
    root = Path(__file__).parent
    
    # PyInstaller arguments
    args = [
        'gui_app.py',  # Main script
        '--name=DigitalHumain',
        '--onefile',  # Single exe file
        '--windowed',  # No console window
        '--clean',
        
        # Add data files
        f'--add-data={root / "config" / "config.yaml"}{";config" if sys.platform == "win32" else ":config"}',
        f'--add-data={root / "digital_humain"}{";digital_humain" if sys.platform == "win32" else ":digital_humain"}',
        
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
        
        # Exclude unnecessary modules
        '--exclude-module=streamlit',
        '--exclude-module=matplotlib',
        '--exclude-module=IPython',
        
        # Output directory
        '--distpath=dist',
        '--workpath=build',
        '--specpath=.',
    ]
    
    print("Building Digital Humain executable...")
    print(f"Output will be in: {root / 'dist' / 'DigitalHumain.exe'}")
    
    PyInstaller.__main__.run(args)
    
    print("\n✅ Build complete!")
    print(f"Executable: {root / 'dist' / 'DigitalHumain.exe'}")
    print("\nNote: Make sure to copy the following alongside the .exe:")
    print("  - config/config.yaml")
    print("  - .env (if using API keys)")
    print("  - screenshots/ folder (will be created automatically)")

if __name__ == "__main__":
    build()
