# Digital Humain - Agentic AI for Enterprise Desktop Automation

A self-hosted Python-based agentic AI framework for enterprise desktop automation, combining LangGraph-based orchestration with Vision Language Models (VLM) for GUI interaction.

## Features

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
- Ollama (for local LLM inference)

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

3. Install and start Ollama:
```bash
# Install Ollama (see https://ollama.ai for instructions)
# Then pull a model
ollama pull llama2

# Start Ollama server
ollama serve
```

4. Configure the system:
```bash
# Edit config/config.yaml to customize settings
# Default configuration uses Ollama with llama2 model
```

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

# Initialize components
llm = OllamaProvider(model="llama2")
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

## GUI Application

### Running from Python

Launch the enhanced GUI with memory and recording features:

```bash
python gui_app.py
```

The GUI includes:
- **LLM Configuration**: Select provider (Ollama/OpenRouter/Letta) and model
- **Task Execution**: Natural language task input with voice support
- **Recording Controls**: Record, save, and replay user demonstrations
- **Memory Settings**: Configure episodic memory and replay speed
- **Execution Logs**: Real-time logging of agent actions and decisions
- **Stop Control**: Interrupt running tasks at any time

### Building Standalone Executable

Create a standalone .exe for Windows distribution:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
python build_exe.py
```

The executable will be created in `dist/DigitalHumain.exe`. 

**Important**: Copy these files alongside the .exe:
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
- Element detection using OCR
- GUI action execution (click, type, scroll, etc.)
- Visual reasoning for automation

### Tool System

Extensible tool framework for:
- File operations (read, write, list)
- System interactions
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

- All LLM inference runs locally (Ollama/vLLM)
- No data sent to external APIs
- Full control over data processing
- Suitable for sensitive enterprise data

## Requirements

See `requirements.txt` for full dependency list. Key dependencies:

- `langgraph`: Agent orchestration
- `langchain`: LLM framework
- `ollama`: Local LLM integration
- `pillow`, `opencv-python`: Image processing
- `pyautogui`: GUI automation
- `pydantic`: Data validation
- `loguru`: Logging

## License

[Add your license here]

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## Support

For issues and questions, please use the GitHub issue tracker.
