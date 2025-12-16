# Digital Humain - Agentic AI for Enterprise Desktop Automation

A self-hosted Python-based agentic AI framework for enterprise desktop automation, combining LangGraph-based orchestration with Vision Language Models (VLM) for GUI interaction.

## Features

### Core Capabilities
- 🤖 **Multi-Agent Orchestration**: Letta-like architecture for coordinating multiple specialized agents
- 👁️ **Vision-Based GUI Interaction**: UI-TARS-like VLM capabilities for understanding and interacting with desktop applications
- 🔒 **Data Privacy**: Local LLM integration (Ollama/vLLM) ensures all data stays on-premises
- 🛠️ **Tool Execution Framework**: Extensible tool system for file operations and automation
- 🧠 **Multi-Step Reasoning**: ReAct-pattern agents with observation, reasoning, and action capabilities
- 📊 **Unstructured Data Handling**: Process various data formats for HBYS, Accounting, and Quality tasks
- 🔄 **Shared Memory**: Context sharing between agents for collaborative task execution
- 🎬 **Learn from User**: Record and replay user demonstrations for macro automation
- 🧩 **Episodic Memory**: Store and retrieve past experiences for enhanced decision making
- 📝 **Memory Summarization**: Rolling summaries prevent prompt bloat in long-running tasks
- 🎨 **Visual Overlay**: Real-time colorful indicators show what the agent is doing (clicks, typing, actions)
- 🚀 **Auto-Discovery**: Automatically finds and launches Desktop apps (Bizmed, HBYS, etc.) without configuration

### Production Features (NEW)
- 🏗️ **Hierarchical Planning**: Two-tier Planner/Worker architecture for long-horizon tasks
- 🔄 **Automatic Recovery**: Explicit error handling with recovery nodes and exponential backoff
- 🛡️ **Security Hardening**: Sandboxing support, prompt injection defense, and credential management
- ⚡ **Performance Optimization**: Tool caching with 1.69x speedup, VLM quantization support
- 📊 **Observability**: Prometheus metrics, structured logging, and audit trails
- 🔀 **Hybrid Deployment**: Flexible local/cloud routing for privacy and performance
- 🎯 **Smart Action Parsing**: Priority-based intent detection with explicit action command recognition
- 🚀 **Auto-Advance Fallback**: Intelligent task progression when LLM returns empty responses

## Documentation

See [docs/README.md](docs/README.md) for the full documentation index (architecture, reports, summaries, prompts, and expert recommendations).

## Architecture

```
digital_humain/
├── core/               # Core agent framework
│   ├── agent.py       # Base agent with ReAct pattern
│   ├── engine.py      # LangGraph-based execution engine
│   └── llm.py         # LLM provider integrations
├── vlm/               # Vision Language Model module
│   ├── screen_analyzer.py  # Screen capture and analysis
│   └── actions.py          # GUI action execution
├── memory/            # Learning and recall systems
│   ├── demonstration.py # Record/replay user actions
│   └── episodic.py    # Episodic memory and summarization
├── orchestration/     # Multi-agent coordination
│   ├── coordinator.py # Task decomposition and delegation
│   ├── registry.py    # Agent registry
│   └── memory.py      # Shared memory for agents
├── tools/             # Tool execution framework
│   ├── base.py        # Tool interface
│   └── file_tools.py  # File operation tools
├── agents/            # Concrete agent implementations
│   └── automation_agent.py  # Desktop automation agent
└── utils/             # Utilities and configuration
    ├── logger.py      # Logging setup
    └── config.py      # Configuration management
```

## Installation

### Prerequisites

- Python 3.9+
- Ollama (for local LLM inference) OR an OpenRouter API key (for cloud fallback)
- Tesseract OCR (for screen text extraction)

### Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| **Linux** | ✅ Full Support | Tested on Ubuntu 22.04+ |
| **Windows** | ✅ Full Support | Windows 10/11 |
| **macOS** | ✅ Supported | Requires additional setup |

### Setup

1. Clone the repository:
```bash
git clone https://github.com/curiousbrutus/digital-humain.git
cd digital-humain
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
```bash
# Linux (Ubuntu/Debian)
sudo apt install tesseract-ocr

# Windows - Download from:
# https://github.com/UB-Mannheim/tesseract/wiki

# macOS
brew install tesseract
```

4. Install screenshot dependencies (Linux only):
```bash
# Required for PyAutoGUI screenshots on Linux
sudo apt install gnome-screenshot scrot
```

5. Install and configure Ollama (see next section)

## LLM & VLM Configuration

Digital Humain supports multiple LLM providers and Vision Language Models for different use cases.

### Ollama (Recommended for Privacy)

Ollama provides local LLM inference - all processing stays on your machine.

```bash
# Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve
```

#### Recommended Models by System Specs

| RAM | GPU VRAM | Recommended Models | Use Case |
|-----|----------|-------------------|----------|
| **8GB** | None | `llama3.2:1b`, `qwen2.5:1.5b` | Basic agent reasoning |
| **16GB** | 2-4GB | `moondream`, `llama3.2:3b` | VLM + reasoning |
| **32GB** | 8GB+ | `llama3.2-vision`, `llava:7b` | Full VLM capabilities |
| **64GB+** | 12GB+ | `llava:13b`, `llama3.1:70b` | Enterprise workloads |

#### Setting Up Moondream (Lightweight VLM)

**Moondream** is ideal for resource-constrained systems - only ~1.7GB and runs on CPU:

```bash
# Pull moondream model
ollama pull moondream

# Test it
ollama run moondream "Describe what you see" --images ./screenshot.png
```

**Moondream capabilities:**
- ✅ Screen/UI element identification
- ✅ Text recognition in images
- ✅ Button/form field detection
- ✅ Layout understanding
- ⚠️ Limited complex reasoning (pair with text LLM)

#### Setting Up Llama 3.2 Vision (Full VLM)

For systems with more resources:

```bash
# Pull llama3.2-vision (requires ~4GB RAM)
ollama pull llama3.2-vision

# Or for text-only reasoning
ollama pull llama3.2
```

#### Configuration

Update `config/config.yaml`:

```yaml
llm:
  provider: ollama
  model: moondream  # or llama3.2, llama3.2-vision, etc.
  base_url: http://localhost:11434
  temperature: 0.7
  timeout: 300
```

### OpenRouter (Cloud Alternative)

For complex tasks or when local resources are limited, use OpenRouter's API:

```yaml
llm:
  provider: openrouter
  openrouter:
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
    default_model: google/gemini-2.0-flash-exp:free
```

**Free models on OpenRouter:**
- `google/gemini-2.0-flash-exp:free` - Fast, good for reasoning
- `meta-llama/llama-3.2-11b-vision-instruct:free` - Vision capable
- `qwen/qwen-2.5-72b-instruct:free` - Strong reasoning

Create `.env` file:
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

### Hybrid Setup (Recommended for Production)

Use local models for privacy-sensitive screen analysis, cloud for complex reasoning:

```python
# Local VLM for screen capture (no data leaves your machine)
screen_analyzer = ScreenAnalyzer(vlm_provider=OllamaProvider(model="moondream"))

# Cloud LLM for complex planning (only sends task descriptions)
planner_llm = OpenRouterProvider(model="google/gemini-2.0-flash-exp:free")
```

### VLM Comparison Table

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **moondream** | 1.7GB | ⚡ Fast | Good | Low-resource systems, basic UI detection |
| **llava:7b** | 4.5GB | Medium | Better | General desktop automation |
| **llama3.2-vision** | 4GB | Medium | Better | Balanced performance |
| **llava:13b** | 8GB | Slow | Best | Complex UI analysis |
| **GPT-4V** (API) | N/A | Fast | Excellent | Maximum accuracy (requires API) |

## Quick Start

### Simple Desktop Automation

```python
from digital_humain.core.agent import AgentConfig, AgentRole
from digital_humain.core.llm import OllamaProvider
from digital_humain.core.engine import AgentEngine
from digital_humain.agents.automation_agent import DesktopAutomationAgent
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.file_tools import FileReadTool

# Initialize components with moondream VLM
llm = OllamaProvider(model="moondream")  # or "llama3.2-vision"
screen_analyzer = ScreenAnalyzer()
gui_actions = GUIActions()
tool_registry = ToolRegistry()
tool_registry.register(FileReadTool())

# Create agent
agent_config = AgentConfig(
    name="automation_agent",
    role=AgentRole.EXECUTOR,
    max_iterations=10
)

agent = DesktopAutomationAgent(
    config=agent_config,
    llm_provider=llm,
    screen_analyzer=screen_analyzer,
    gui_actions=gui_actions,
    tool_registry=tool_registry
)

# Execute task
engine = AgentEngine(agent)
result = engine.run("Analyze the current screen and identify key elements")
```

### Using VLM for Screen Analysis

```python
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.core.llm import OllamaProvider

# Initialize with moondream for lightweight VLM
vlm = OllamaProvider(model="moondream")
analyzer = ScreenAnalyzer(vlm_provider=vlm, save_screenshots=True)

# Capture and analyze current screen
result = analyzer.analyze_screen("Find the login button")
print(result)

# Get screen info
info = analyzer.get_screen_info()
print(f"Screen size: {info['screen_size']}")
print(f"Mouse position: {info['mouse_position']}")
```

### Multi-Agent Orchestration

```python
from digital_humain.orchestration.coordinator import AgentCoordinator
from digital_humain.orchestration.registry import AgentRegistry
from digital_humain.orchestration.memory import SharedMemory

# Create coordinator
registry = AgentRegistry()
memory = SharedMemory()
coordinator = AgentCoordinator(registry=registry, memory=memory)

# Register agents
coordinator.register_agent(planner_agent)
coordinator.register_agent(executor_agent)
coordinator.register_agent(analyzer_agent)

# Execute complex task
result = coordinator.execute_task(
    "Analyze the accounting software, plan data entry steps, and execute the workflow"
)
```

## Examples

Run the provided examples:

```bash
# Simple automation example
python examples/simple_automation.py

# Multi-agent orchestration example
python examples/multi_agent_orchestration.py

# Memory and learning features demo
python examples/memory_demo.py
```

## GUI Applications

### Letta-Style GUI ⭐ NEW

Professional interface with advanced memory management inspired by Letta:

```bash
python gui_app_letta.py
```

**Key Features:**
- 🧠 **Core Memory Blocks**: Human context (2000 chars) + Persona definition (2000 chars) with live character counters
- 📚 **Archival Memory**: Long-term storage with search, add/view/delete capabilities
- 💬 **Rich Conversations**: Timestamped messages with agent reasoning display
- 📊 **Token Tracking**: Real-time context window usage with color-coded progress bar
- 🎨 **Professional Design**: Three-panel Letta-inspired layout (Settings | Simulator | Context)
- 🔍 **Memory Search**: Keyword-based retrieval across archival storage
- 📝 **Structured Context**: Enforced character limits prevent context overflow

See [docs/LETTA_GUI.md](docs/LETTA_GUI.md) for complete documentation.

### Standard GUI

Original feature-complete interface:

```bash
python gui_app.py
```

The GUI includes:
- **LLM Configuration**: Select provider (Ollama/OpenRouter/Letta) and model
  - **Health Indicator**: Colored dot (green/red) shows provider connection status - hover for details
- **Task Execution**: Natural language task input with voice support
- **Recording Controls**: Record, save, and replay user demonstrations
- **Memory Settings**: Configure episodic memory and replay speed
- **Execution Logs**: Real-time logging of agent actions and decisions
- **Stop Control**: Interrupt running tasks at any time
- **Visual Indicators**: Toggle real-time action overlays (clicks, typing)

Notes:
- On startup, the app auto-detects which provider is available (Ollama first, then OpenRouter if `OPENROUTER_API_KEY` is set).
- The health indicator (colored dot) shows provider status: green = connected, red = unavailable/misconfigured.
- If Ollama is not installed or the service is not running, the app automatically falls back to OpenRouter when `OPENROUTER_API_KEY` is set.
- You can manually switch providers from the LLM Configuration panel at any time.

### Building Standalone Executable

Create a standalone executable for distribution:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
python build_exe.py
```

**Output by platform:**
- **Windows**: `dist/DigitalHumain.exe`
- **Linux**: `dist/DigitalHumain`
- **macOS**: `dist/DigitalHumain.app`

**Important**: Copy these files alongside the executable:
- `config/config.yaml` - Application configuration
- `.env` - API keys (optional, see below)
- Create an empty `screenshots/` folder for screen captures

- Create a `.env` file in the project root and add any secrets, e.g.:
    - `OPENROUTER_API_KEY=sk-...`
    - `LETTA_API_KEY=...` and `LETTA_AGENT_ID=...`
- The app auto-loads `.env` on startup; the GUI pre-fills the API key field from the environment.
- You can still override in the GUI and click **Set Env** to update the in-session environment without editing files.

See [MEMORY_FEATURES.md](MEMORY_FEATURES.md) for detailed documentation on the memory system.

## Configuration

Edit `config/config.yaml` to customize:

- LLM provider and model settings
- VLM configuration
- Agent behavior parameters
- Logging settings
- Tool configurations

## Core Concepts

### Agents

Agents follow the ReAct (Reasoning + Acting) pattern:
1. **Observe**: Analyze current state
2. **Reason**: Determine next action using LLM
3. **Act**: Execute the action
4. **Repeat**: Continue until task complete

### Multi-Agent Orchestration

The coordinator:
1. Decomposes complex tasks into subtasks
2. Selects appropriate agents for each subtask
3. Manages shared memory for context
4. Aggregates results

### VLM Integration

Vision capabilities include:
- Screen capture and analysis
- Element detection using OCR (Tesseract) and VLM
- GUI action execution (click, type, scroll, etc.)
- Visual reasoning for automation

**Supported VLM workflows:**

| Workflow | Local Model | Cloud Alternative |
|----------|-------------|-------------------|
| UI Element Detection | moondream | GPT-4V |
| Text Extraction | Tesseract OCR | Google Vision |
| Screen Understanding | llama3.2-vision | Claude Vision |
| Action Planning | llama3.2 | GPT-4 |

### Desktop Application Discovery

Automatically discovers and launches applications on your computer:

- **Auto-Scan**: Finds `.exe` and `.lnk` files on Desktop and in Program Files
- **Natural Language**: Say "Open Bizmed" or "Launch HBYS" - no configuration needed
- **Fuzzy Matching**: Partial names work (e.g., "biz" matches "bizmed")
- **Desktop Priority**: Your Desktop shortcuts take precedence

See [docs/APP_DISCOVERY.md](docs/APP_DISCOVERY.md) for full details.

**Test what's discovered:**
```bash
python test_app_discovery.py
```

### Tool System

Extensible tool framework for:
- File operations (read, write, list)
- System interactions
- Desktop application launching
- Custom tool development

## Use Cases

### HBYS (HR/Business Systems)
- Automated data entry
- Form filling and submission
- Report generation
- Workflow automation

### Accounting
- Invoice processing
- Data reconciliation
- Financial report automation
- Audit trail management

### Quality Assurance
- Automated testing workflows
- Compliance checking
- Documentation verification
- Issue tracking automation

## Development

### Adding Custom Agents

```python
from digital_humain.core.agent import BaseAgent, AgentConfig

class MyCustomAgent(BaseAgent):
    def reason(self, state, observation):
        # Implement reasoning logic
        pass
    
    def act(self, state, reasoning):
        # Implement action logic
        pass
```

### Adding Custom Tools

```python
from digital_humain.tools.base import BaseTool, ToolMetadata

class MyCustomTool(BaseTool):
    def get_metadata(self):
        return ToolMetadata(
            name="my_tool",
            description="My custom tool",
            parameters=[...]
        )
    
    def execute(self, **kwargs):
        # Implement tool logic
        pass
```

## Security & Privacy

- All LLM inference runs locally (Ollama/vLLM) by default
- VLM screen analysis happens on-device with moondream
- No data sent to external APIs unless explicitly configured
- Full control over data processing
- Suitable for sensitive enterprise data
- Optional cloud fallback for complex reasoning tasks

## Troubleshooting

### Common Issues

**Ollama connection error:**
```bash
# Make sure Ollama is running
ollama serve

# Check if it's accessible
curl http://localhost:11434/api/tags
```

**Tesseract not found:**
```bash
# Linux
sudo apt install tesseract-ocr

# Verify installation
tesseract --version
```

**PyAutoGUI display issues (Linux):**
```bash
# Install required X11 libraries and screenshot tools
sudo apt install scrot gnome-screenshot python3-tk python3-dev
```

**Numpy/OpenCV binary incompatibility:**
```bash
# If you see "numpy.dtype size changed" error:
pip install "numpy>=1.24,<2.0"
pip install "opencv-python-headless>=4.8,<4.12"
```

**Out of memory with VLM:**
```bash
# Use a smaller model
ollama pull moondream  # Only 1.7GB

# Or use quantized versions
ollama pull llama3.2-vision:4bit
```

## Requirements

See `requirements.txt` for full dependency list. Key dependencies:

- `langgraph`: Agent orchestration
- `langchain`: LLM framework
- `ollama`: Local LLM integration
- `pillow`, `opencv-python-headless`: Image processing
- `numpy>=1.24,<2.0`: Array operations (version constrained for compatibility)
- `pyautogui`: GUI automation
- `gnome-screenshot` (Linux): Screenshot capture
- `pytesseract`: OCR text extraction
- `pydantic`: Data validation
- `loguru`: Logging
- `pynput`: Action recording

## License

[Add your license here]

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## Support

For issues and questions, please use the GitHub issue tracker.
