# Installation Guide - Digital Humain

Installation methods for different systems and use cases.

## Quick Install (All Systems)

### Prerequisites
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Git** (for cloning repository)
- **Ollama** (for local LLM) - [Download](https://ollama.ai)
- **Tesseract OCR** (for text extraction)

### Step 1: Clone Repository
```bash
git clone https://github.com/curiousbrutus/digital-humain.git
cd digital-humain
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Digital Humain
```bash
# Basic installation
pip install .

# OR with development tools
pip install -e .[dev]

# OR with GUI support
pip install -e .[gui]

# OR everything
pip install -e .[all]
```

### Step 4: Verify Installation
```bash
# Test import
python -c "import digital_humain; print('✅ Installation successful!')"

# Run GUI app
python gui_main.py
```

---

## Installation by Use Case

### 👤 For End Users (Simple GUI Usage)
```bash
pip install .
python gui_main.py
```

### 👨‍💻 For Developers (Contributing Code)
```bash
pip install -e .[dev]
pytest tests/                    # Run tests
python -m black .               # Format code
python -m flake8 .              # Lint code
```

### 🏗️ For Building Executables
```bash
pip install -e .[build]
python scripts/build_exe.py     # Creates dist/DigitalHumain.exe
```

### 🔬 For Research/Experimentation
```bash
pip install -e .[all]          # Everything
python examples/simple_automation.py
```

---

## Installation by Operating System

### 🪟 Windows 10/11

#### Option A: Automated Installation
```powershell
# Run as Administrator
python -m pip install --upgrade pip
git clone https://github.com/curiousbrutus/digital-humain.git
cd digital-humain
python -m venv venv
venv\Scripts\activate
pip install -e .[all]
python gui_main.py
```

#### Option B: Standalone Executable (No Python Needed)
```powershell
# Download pre-built executable from releases
# Or build it yourself:
pip install -e .[build]
python scripts/build_exe.py
# Creates: dist/DigitalHumain.exe (~170 MB)
```

#### Tesseract OCR (Required for Text Recognition)
```powershell
# Download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Or use chocolatey:
choco install tesseract

# Or use scoop:
scoop install tesseract
```

---

### 🐧 Ubuntu/Debian Linux

```bash
# Update package manager
sudo apt update && sudo apt upgrade

# Install dependencies
sudo apt install python3.11 python3.11-venv python3-pip git

# Install Tesseract
sudo apt install tesseract-ocr libtesseract-dev

# Clone and install Digital Humain
git clone https://github.com/curiousbrutus/digital-humain.git
cd digital-humain
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .[all]

# Run
python gui_main.py
```

---

### 🍎 macOS

```bash
# Using Homebrew
brew install python@3.11 git tesseract

# Clone and install
git clone https://github.com/curiousbrutus/digital-humain.git
cd digital-humain
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .[all]

# Run
python gui_main.py
```

---

## Troubleshooting

### Problem: "Python not found"
```bash
# Windows: Make sure Python is in PATH
python --version

# Linux/Mac: Use python3
python3 --version
```

### Problem: "Permission denied" (Linux/Mac)
```bash
# Add executable permission
chmod +x gui_main.py
```

### Problem: "Tesseract not found"
```bash
# Windows: Add to PATH manually or reinstall
# Linux: sudo apt install tesseract-ocr
# Mac: brew install tesseract
```

### Problem: "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install --upgrade --force-reinstall -r requirements.txt
```

### Problem: GUI doesn't appear
```bash
# Test if Tkinter is installed
python -m tkinter

# If fails, install:
# Ubuntu: sudo apt install python3-tk
# Fedora: sudo dnf install python3-tkinter
# macOS: Usually included with Python
```

### Problem: OCR/Tesseract errors
```bash
# Test if Tesseract is in PATH
tesseract --version

# If not found, add to Python:
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## Virtual Environment Management

### Create Virtual Environment
```bash
python -m venv venv
```

### Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Delete Virtual Environment
```bash
# Windows
rmdir /s venv

# Linux/Mac
rm -rf venv
```

---

## Upgrading Digital Humain

```bash
# From project directory
git pull origin main
pip install --upgrade -e .[all]
```

---

## Uninstalling

```bash
# From project directory
pip uninstall digital-humain

# Delete the project folder
rm -rf digital-humain  # Linux/Mac
rmdir /s digital-humain  # Windows
```

---

## Running the Application

### Start GUI Application
```bash
python gui_main.py
```

### Start Letta Integration GUI
```bash
python gui_letta.py
```

### Use as Python Module
```python
from digital_humain.agents.automation_agent import DesktopAutomationAgent
from digital_humain.core.agent import AgentConfig

config = AgentConfig(
    name="my_agent",
    role="executor",
    model="llama2"
)

agent = DesktopAutomationAgent(config)
result = agent.execute("Open Notepad and write 'Hello World'")
print(result)
```

### Run Tests
```bash
pytest tests/                    # All tests
pytest tests/unit/              # Unit tests only
pytest tests/e2e/               # End-to-end tests only
pytest tests/ -v                # Verbose output
```

### Build Standalone Executable
```bash
python scripts/build_exe.py
# Creates: dist/DigitalHumain.exe
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, Ubuntu 20.04, macOS 10.15 | Windows 11, Ubuntu 22.04, macOS 12+ |
| **Python** | 3.9 | 3.11+ |
| **RAM** | 2 GB | 8 GB+ |
| **Storage** | 500 MB | 2 GB (with models) |
| **GPU** | Optional | NVIDIA CUDA (for faster inference) |

---

## Configuration

### Environment Variables
Create a `.env` file in project root:
```env
# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama2

# OpenRouter (if using cloud)
OPENROUTER_API_KEY=your_key_here

# Letta (if using Letta)
LETTA_API_KEY=your_key_here
LETTA_AGENT_ID=agent_id

# Logging
LOG_LEVEL=INFO
LOG_DIR=./data/logs
```

### Configuration File
Edit `config/config.yaml`:
```yaml
llm:
  provider: ollama        # ollama, openrouter, or letta
  model: llama2
  temperature: 0.7

vlm:
  save_screenshots: true
  screenshot_dir: ./data/screenshots

memory:
  episodic_enabled: true
  episodic_path: ./data/episodic_memory
```

---

## Frequently Asked Questions

### Q: Do I need a GPU?
A: No, but it speeds up LLM inference significantly.

### Q: Can I use this without Ollama?
A: Yes, you can use OpenRouter (cloud) or Letta instead.

### Q: What's the typical installation time?
A: 5-10 minutes with all dependencies, first run may take longer as models download.

### Q: Is it safe to install multiple times?
A: Yes, reinstalling/upgrading is safe and recommended.

### Q: Can I use it in a Docker container?
A: Yes, see DEPLOYMENT.md for Docker setup.

---

## Getting Help

- **Documentation**: See `docs/` folder
- **Issues**: [GitHub Issues](https://github.com/curiousbrutus/digital-humain/issues)
- **Discussions**: [GitHub Discussions](https://github.com/curiousbrutus/digital-humain/discussions)

---

**Happy installing! Questions? Check the troubleshooting section or open an issue.** 🚀
