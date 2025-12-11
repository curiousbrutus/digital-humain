# Digital Humain - Architecture Overview

## System Architecture

Digital Humain is a self-hosted agentic AI framework designed for enterprise desktop automation with a focus on data privacy and multi-step reasoning.

## Core Components

### 1. Agent Framework (`core/`)

#### BaseAgent (`core/agent.py`)
- Implements the ReAct (Reasoning + Acting) pattern
- Maintains agent state throughout execution
- Provides abstract methods for reasoning and action
- Supports multi-step reasoning with observation history

**Key Classes:**
- `AgentState`: TypedDict for agent execution state
- `AgentConfig`: Pydantic model for agent configuration
- `AgentRole`: Enum for agent specializations (COORDINATOR, EXECUTOR, ANALYZER, PLANNER)
- `BaseAgent`: Abstract base class for all agents

#### AgentEngine (`core/engine.py`)
- LangGraph-based execution engine
- Builds state graphs for agent workflows
- Manages transitions between observe, reason, and act nodes
- Supports both synchronous and asynchronous execution

#### LLM Providers (`core/llm.py`)
- `OllamaProvider`: Local inference with Ollama
- `VLLMProvider`: High-performance inference with vLLM
- Supports model management (list, pull models)
- Configurable temperature, max tokens, and stop sequences

### 2. Vision Language Model (`vlm/`)

#### ScreenAnalyzer (`vlm/screen_analyzer.py`)
- Captures screenshots of entire screen or regions
- Analyzes screen content using VLM or OCR fallback
- Finds UI elements by description
- Manages screenshot storage for debugging

**Capabilities:**
- Screen capture with region support
- VLM-based analysis (when provider available)
- OCR-based fallback using Tesseract
- Element detection with bounding boxes
- Screenshot persistence

#### GUIActions (`vlm/actions.py`)
- Executes desktop automation actions
- Supports mouse, keyboard, and scroll operations
- Maintains action history
- Configurable pause and safe mode

**Action Types:**
- Click (single, double, right-click)
- Type text with configurable intervals
- Press keys and hotkey combinations
- Move mouse with smooth transitions
- Scroll operations
- Drag operations
- Wait/delay

### 3. Multi-Agent Orchestration (`orchestration/`)

#### AgentCoordinator (`orchestration/coordinator.py`)
- Decomposes complex tasks into subtasks
- Selects appropriate agents for each subtask
- Delegates tasks and aggregates results
- Manages execution history

**Workflow:**
1. Task decomposition based on keywords and patterns
2. Agent selection by role matching
3. Task delegation with shared context
4. Result aggregation and memory updates

#### AgentRegistry (`orchestration/registry.py`)
- Manages agent lifecycle
- Provides agent lookup by name or role
- Lists available agents and their capabilities
- Supports dynamic agent registration/unregistration

#### SharedMemory (`orchestration/memory.py`)
- Centralized memory for inter-agent communication
- Tracks memory operation history
- Supports get, set, update, delete operations
- Provides snapshots and statistics

### 4. Tool System (`tools/`)

#### BaseTool (`tools/base.py`)
- Abstract interface for tools
- Parameter validation
- Metadata definition with Pydantic

#### ToolRegistry (`tools/base.py`)
- Tool registration and lookup
- Tool execution with error handling
- Metadata management

#### File Tools (`tools/file_tools.py`)
- `FileReadTool`: Read file contents
- `FileWriteTool`: Write/append to files
- `FileListTool`: List files with glob patterns

### 5. Concrete Agents (`agents/`)

#### DesktopAutomationAgent (`agents/automation_agent.py`)
- Specialized for desktop automation tasks
- Integrates LLM, VLM, and GUI actions
- Implements reasoning and action methods
- Parses natural language to actions
- Determines task completion

**Features:**
- Screen analysis for UI understanding
- Action parsing from reasoning text
- Tool integration for file operations
- Configurable completion criteria

## Data Flow

```
User Task
    ↓
AgentCoordinator
    ↓
Task Decomposition
    ↓
[Subtask 1] → [Agent Selection] → [DesktopAutomationAgent]
                                        ↓
                                   Agent Loop:
                                   1. Observe (Screen Analysis)
                                   2. Reason (LLM)
                                   3. Act (GUI Actions/Tools)
                                        ↓
                                   SharedMemory ← Context
                                        ↓
[Subtask 2] → [Agent Selection] → [DesktopAutomationAgent]
    ↓
Result Aggregation
    ↓
User
```

## Design Patterns

### ReAct Pattern
The core agent loop implements the ReAct pattern:
1. **Observe**: Gather information about current state
2. **Reason**: Use LLM to determine next action
3. **Act**: Execute the determined action
4. **Repeat**: Continue until task completion

### State Graph Pattern
Using LangGraph for workflow management:
- Nodes represent stages (observe, reason, act)
- Edges define transitions
- Conditional edges for branching logic
- State flows through the graph

### Registry Pattern
For managing agents and tools:
- Centralized registration
- Lookup by name or type
- Dynamic addition/removal
- Metadata tracking

## Configuration System

### YAML Configuration (`config/config.yaml`)
Hierarchical configuration for:
- LLM provider settings
- VLM configuration
- Agent parameters
- Logging settings
- Tool configurations

### Environment Variables
Sensitive settings can be overridden via environment:
- `OLLAMA_BASE_URL`
- `LLM_MODEL`
- `LOG_LEVEL`

## Security & Privacy

### Local Inference
- All LLM inference happens locally
- No external API calls for reasoning
- Full control over data

### Data Isolation
- Agents work on local files
- Screenshots stored locally
- Memory stays in process

### Safe Mode
- GUI automation includes fail-safe
- Configurable pause between actions
- Action history for debugging

## Extensibility

### Adding Custom Agents
Extend `BaseAgent` and implement:
- `reason()`: LLM-based reasoning logic
- `act()`: Action execution logic
- Optional: Custom `observe()` and `should_continue()`

### Adding Custom Tools
Extend `BaseTool` and implement:
- `get_metadata()`: Tool description and parameters
- `execute()`: Tool logic
- Register with `ToolRegistry`

### Adding Custom VLM Providers
Extend `LLMProvider` for vision models:
- Implement image-to-text generation
- Handle image encoding
- Support multimodal prompts

## Performance Considerations

### LLM Inference
- Local inference may be slower than cloud
- Model size affects performance
- vLLM recommended for production (higher throughput)

### Screen Analysis
- OCR fallback is faster than VLM
- Screenshot size affects processing time
- Region capture reduces overhead

### Memory Usage
- LLM models require significant RAM
- Screenshot history grows over time
- Shared memory is in-process only

## Future Enhancements

1. **Enhanced VLM Integration**: Support for LLaVA and other vision models
2. **Persistent Memory**: Redis/database backend for shared memory
3. **Advanced Task Planning**: LLM-based task decomposition
4. **Tool Learning**: Dynamic tool discovery and usage
5. **Web Automation**: Selenium/Playwright integration
6. **API Integration**: REST API for remote control
7. **Monitoring**: Metrics and observability
8. **Agent Learning**: Fine-tuning from execution history
