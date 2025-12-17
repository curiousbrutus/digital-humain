# SOMA Architecture - Self-Organizing Modular Agent

## Overview

Digital Humain has been transformed into a production-grade, vision-centric AI desktop automation agent using the **Self-Organizing Modular Agent (SOMA)** architecture. The system now supports **Learning from Demonstration (LfD)** via screen recordings and utilizes **Hierarchical Memory Management (HMM)** for infinite context.

## Core Principles

1. **Micro-Modular Design**: No monolithic controller - specialized modules work independently
2. **Vision-First**: Pure vision-based UI element detection and coordinate mapping
3. **Learning from Demonstration**: Learn workflows from recorded user actions
4. **Infinite Context**: Hierarchical memory with virtual context paging
5. **Robust Recovery**: Audit trails and checkpoints for error recovery

## Architecture Components

### 1. Orchestration Engine (OE)
**Location**: `digital_humain/core/orchestration_engine.py`

Central control plane for task decomposition and tool routing.

**Key Features**:
- **Task Decomposition**: Breaks complex tasks into subtasks
- **Tool Routing**: Routes tools based on task requirements
- **Execution Planning**: Creates detailed plans with dependency resolution
- **Context Management**: Integrates with HMM for context

**Usage**:
```python
from digital_humain.core.orchestration_engine import OrchestrationEngine

oe = OrchestrationEngine()

# Decompose a task
decomposition = oe.decompose_task("Open browser and fill out form")

# Create execution plan
plan = oe.create_execution_plan(decomposition)
```

### 2. Perception & Grounding VLM (PG-VLM)
**Location**: `digital_humain/vlm/screen_analyzer.py`, `digital_humain/learning/action_recognition.py`

Pure vision-based UI element detection and coordinate mapping.

**Key Features**:
- **Screen Analysis**: Captures and analyzes screenshots
- **Element Detection**: Identifies UI elements using VLM
- **Action Recognition**: Recognizes actions from screen + events
- **Semantic Grounding**: Maps visual elements to semantic labels

**Usage**:
```python
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.learning.action_recognition import ActionRecognitionEngine

analyzer = ScreenAnalyzer()
recognizer = ActionRecognitionEngine()

# Analyze screen
screenshot = analyzer.capture_screen()
elements = recognizer.analyze_screenshot(screenshot_path)
```

### 3. Hierarchical Memory Manager (HMM)
**Location**: `digital_humain/memory/hierarchical_memory.py`

Virtual context paging (MemGPT-style) between RAM (LLM context) and Disk (AKB).

**Key Features**:
- **Main Context**: Active prompt window (RAM)
- **External Context**: Agent Knowledge Base (Disk)
- **Paging**: Dynamic swapping between contexts
- **Priority-Based**: LRU with priority considerations

**Usage**:
```python
from digital_humain.memory.hierarchical_memory import HierarchicalMemoryManager

hmm = HierarchicalMemoryManager()

# Add to context
hmm.add_to_context("current_task", {"task": "fill form"}, priority=8)

# Page out older items
hmm.page_out(["old_task_1", "old_task_2"])

# Page in relevant items
hmm.search_and_page_in("form filling", limit=3)
```

### 4. Audit & Recovery Engine (ARE)
**Location**: `digital_humain/core/audit_recovery.py`

Reasoning chain logger and state checkpoint manager.

**Key Features**:
- **Reasoning Logs**: Capture Chain-of-Thought for every action
- **Checkpoints**: Save state at sub-task completion
- **Recovery Context**: Feed error state back for self-correction
- **Confidence Tracking**: Track confidence scores

**Usage**:
```python
from digital_humain.core.audit_recovery import AuditRecoveryEngine

are = AuditRecoveryEngine()

# Log reasoning
are.log_reasoning(
    step=1,
    observation="Login form visible",
    reasoning="Need to enter credentials",
    action={"type": "click", "target": "username_field"},
    confidence=0.95
)

# Create checkpoint
are.create_checkpoint(
    task="Login to system",
    step=5,
    state_snapshot={"logged_in": True}
)

# Get recovery context on error
recovery_ctx = are.get_recovery_context("Login failed", recent_steps=3)
```

### 5. Trajectory Abstraction Service (TAS)
**Location**: `digital_humain/learning/trajectory_abstraction.py`

Processes raw recordings into Generalized Workflows.

**Key Features**:
- **Recording Ingestion**: Processes MP4/WebM + JSON events + descriptions
- **Action Recognition**: Uses VLM to detect UI elements at event timestamps
- **Workflow Abstraction**: Creates semantic actions (e.g., `click(label="Submit")`)
- **Memory Extraction**: Extracts narrative (why) and episodic (how) memories

**Usage**:
```python
from digital_humain.learning.trajectory_abstraction import TrajectoryAbstractionService

tas = TrajectoryAbstractionService()

# Process recording directory
workflow = tas.process_recording_directory("./recordings/my_workflow")

# Save workflow
workflow.save("./demonstrations")
```

### 6. Workflow Definition Language (WDL)
**Location**: `digital_humain/learning/workflow_definition.py`

JSON schema for generalized workflows with semantic actions.

**Key Components**:
- **Narrative Memory**: The 'why' - goal and user intent
- **Episodic Memory**: The 'how' - execution details
- **Workflow Steps**: Sequence of semantic actions
- **Versioning**: Changelog and version control
- **Access Control**: Permissions and ACL

**Example WDL**:
```json
{
  "id": "abc123",
  "name": "Login to Application",
  "version": "1.0.0",
  "narrative_memory": {
    "goal": "Authenticate user into system",
    "user_intent": "User wants to access their account",
    "success_criteria": ["User is logged in", "Dashboard is visible"]
  },
  "episodic_memory": {
    "application": "MyApp v2.0",
    "key_ui_elements": ["Username field", "Password field", "Login button"],
    "timing_info": {"total_duration": 15.5}
  },
  "steps": [
    {
      "step_number": 1,
      "description": "Enter username",
      "actions": [
        {
          "action_type": "click",
          "target": "Username field"
        },
        {
          "action_type": "type",
          "target": "Username field",
          "value": "user@example.com"
        }
      ]
    }
  ]
}
```

## Learning from Demonstration (LfD) Pipeline

### Recording Structure

Recordings should be organized in directories with this structure:

```
demonstrations/
└── my_workflow/
    ├── video.mp4              # Screen recording
    ├── events.json            # Mouse/keyboard events
    ├── metadata.json          # Metadata (optional)
    └── screenshots/           # Extracted frames (optional)
        ├── frame_0000.png
        ├── frame_0001.png
        └── ...
```

### Processing Pipeline

1. **Record**: Capture screen + events
2. **Recognize**: VLM detects UI elements at event timestamps
3. **Abstract**: Distill into semantic WDL
4. **Generalize**: Extract narrative and episodic memory
5. **Register**: Add to workflow library

```python
from digital_humain.learning.trajectory_abstraction import TrajectoryAbstractionService
from digital_humain.learning.workflow_definition import WorkflowLibrary

# Process recording
tas = TrajectoryAbstractionService()
workflow = tas.process_recording_directory("./demonstrations/my_workflow")

# Add to library
library = WorkflowLibrary()
library.add_workflow(workflow)

# Search workflows
results = library.search_workflows("login")
```

## Tool Schema

### Browser Tools
- `browser_navigate`: Navigate to URL
- `browser_click`: Click element
- `browser_fill`: Fill form field
- `browser_wait`: Wait for element/condition
- `browser_get_text`: Extract text
- `browser_screenshot`: Take screenshot

### System Tools
- `system_launch_app`: Launch application
- `system_window_management`: Manage windows
- `system_clipboard`: Clipboard operations
- `system_process_control`: Control processes
- `system_screen_info`: Get screen info

### File Tools
- `file_read`: Read file
- `file_write`: Write/append file
- `file_list`: List files with patterns

### Learning Tools
- `record_demo`: Record demonstration
- `process_recording`: Process into workflow
- `register_workflow`: Register in library
- `list_workflows`: List workflows
- `search_workflows`: Search workflows
- `get_workflow`: Get specific workflow

## Perception & Action Loop

Agents follow a strict loop:

1. **Observe**: Capture screenshot and parse via PG-VLM
2. **Reason**: Compare state against WDL/Goal
3. **Act**: Execute bounded action (click, type, scroll, hotkey)
4. **Audit**: Record reasoning and confidence in ARE log

```python
from digital_humain.core.audit_recovery import AuditRecoveryEngine
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer

are = AuditRecoveryEngine()
screen_analyzer = ScreenAnalyzer()

# Observe
screenshot = screen_analyzer.capture_screen()
observation = screen_analyzer.analyze_screen("Find submit button")

# Reason (using LLM)
reasoning = llm.generate(f"Given observation: {observation}, what action to take?")

# Act
action_result = gui_actions.click(position=(100, 200))

# Audit
are.log_reasoning(
    step=current_step,
    observation=observation,
    reasoning=reasoning,
    action=action_result,
    confidence=0.9
)

# Check if checkpoint needed
if are.should_checkpoint(current_step):
    are.create_checkpoint(
        task="Submit form",
        step=current_step,
        state_snapshot=current_state
    )
```

## Integration Examples

### Full SOMA Agent

```python
from digital_humain.core.orchestration_engine import OrchestrationEngine
from digital_humain.memory.hierarchical_memory import HierarchicalMemoryManager
from digital_humain.core.audit_recovery import AuditRecoveryEngine
from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.browser_tools import *
from digital_humain.tools.system_tools import *

# Initialize SOMA components
oe = OrchestrationEngine()
hmm = HierarchicalMemoryManager()
are = AuditRecoveryEngine()

# Register tools
tool_registry = ToolRegistry()
tool_registry.register(BrowserNavigateTool())
tool_registry.register(BrowserClickTool())
tool_registry.register(LaunchAppTool())

# Decompose and execute task
task = "Open browser, navigate to example.com, and click login"
decomposition = oe.decompose_task(task)

for subtask in decomposition.subtasks:
    # Get context for subtask
    context = oe.get_context_for_subtask(subtask, decomposition)
    
    # Execute subtask (delegate to agent)
    # ... execution logic ...
    
    # Update status
    oe.update_subtask_status(subtask.id, TaskStatus.COMPLETED)
```

### Workflow Execution

```python
from digital_humain.learning.workflow_definition import WorkflowLibrary

library = WorkflowLibrary()

# Get workflow
workflow = library.get_workflow("abc123")

# Execute workflow steps
for step in workflow.steps:
    print(f"Step {step.step_number}: {step.description}")
    
    for action in step.actions:
        # Execute action
        if action.action_type == "click":
            gui_actions.click_element(action.target)
        elif action.action_type == "type":
            gui_actions.type_text(action.target, action.value)
```

## Configuration

SOMA components can be configured via `config/config.yaml`:

```yaml
soma:
  hmm:
    max_main_context_size: 10000
    page_size: 1000
    akb_storage_path: ./agent_knowledge_base
  
  are:
    checkpoint_cadence: 5
    max_logs: 10000
    storage_path: ./audit_logs
  
  tas:
    confidence_threshold: 0.7
    demonstrations_dir: ./demonstrations
  
  oe:
    max_subtasks: 20
    parallel_execution: false
```

## Performance Considerations

- **Context Management**: HMM keeps main context under 10K tokens
- **Paging Overhead**: Page in/out operations take ~100ms
- **VLM Analysis**: Screen analysis takes 1-3s depending on model
- **Checkpoint Frequency**: Balance between recovery and performance

## Security

- **ACL**: Workflows have access control lists
- **Secret Filtering**: ARE filters sensitive data
- **Sandboxing**: Tools can be sandboxed (future enhancement)
- **Audit Trail**: Complete reasoning chain for forensics

## Future Enhancements

1. **Enhanced VLM Integration**: Support for more vision models
2. **Multi-Modal Learning**: Audio + video + text recordings
3. **Workflow Optimization**: Automatic workflow optimization
4. **Collaborative Learning**: Share workflows between agents
5. **Real-time Adaptation**: Adapt workflows to UI changes
6. **Performance Profiling**: Detailed execution metrics

## References

- [MemGPT Paper](https://arxiv.org/abs/2310.08560) - Hierarchical Memory
- [ReAct Paper](https://arxiv.org/abs/2210.03629) - Reasoning + Acting
- [OmniParser](https://microsoft.github.io/OmniParser/) - UI Parsing
- [UI-TARS](https://arxiv.org/abs/2401.13282) - Vision-based UI automation
