# Memory & Learning Features

Digital Humain now includes advanced memory and learning-from-user capabilities that enable the agent to record, replay, and learn from user demonstrations.

## Features Overview

### 1. Demonstration Memory (Record & Replay)

The demonstration memory system allows you to record user mouse and keyboard actions and replay them later. This enables:

- **Learning by demonstration**: Show the agent what to do once, and it can repeat it
- **Macro creation**: Record complex sequences of actions for automation
- **Testing & validation**: Create repeatable test scenarios

#### Key Components

- **ActionRecorder**: Captures real-time mouse clicks, movements, and keyboard events
- **RecordedAction**: Stores individual actions with timestamps, window context, and screen metadata
- **DemonstrationMemory**: Manages saving, loading, and replaying demonstrations

#### Usage

```python
from digital_humain.memory.demonstration import DemonstrationMemory

# Initialize demonstration memory
demo_memory = DemonstrationMemory(storage_path="./demonstrations")

# Start recording
demo_memory.start_recording()

# Perform actions... (mouse clicks, keyboard typing, etc.)

# Stop recording
actions = demo_memory.stop_recording()

# Save the recording
demo_memory.save_demonstration(
    name="my_workflow",
    actions=actions,
    metadata={"description": "Daily workflow automation"}
)

# List available demonstrations
demos = demo_memory.list_demonstrations()

# Replay a demonstration
results = demo_memory.replay_demonstration(
    name="my_workflow",
    speed=1.0,           # Playback speed (0.5x to 2.0x)
    dry_run=False,       # Set to True to preview actions without executing
    safety_pause=True    # 3-second delay before replay starts
)
```

### 2. Episodic Memory

Episodic memory stores summarized observations, reasonings, and actions from agent execution. This enables:

- **Learning from experience**: Agent can recall similar past situations
- **Context-aware decision making**: Retrieve relevant past episodes for current tasks
- **Knowledge accumulation**: Build up a knowledge base over time

#### Key Components

- **Episode**: Stores a single agent experience with observation, reasoning, action, and result
- **EpisodicMemory**: Manages storage, retrieval, and querying of episodes
- **Guardrails**: Automatic filtering of secrets and sensitive information

#### Usage

```python
from digital_humain.memory.episodic import EpisodicMemory

# Initialize episodic memory
memory = EpisodicMemory(
    storage_path="./episodic_memory",
    max_episodes=1000,
    enable_recall=True
)

# Add an episode
episode = memory.add_episode(
    observation="User clicked on submit button",
    reasoning="Form is complete, ready to submit",
    action={"type": "click", "target": "submit_btn"},
    result="Form submitted successfully",
    metadata={"task": "form_submission", "user": "alice"}
)

# Retrieve relevant episodes
relevant = memory.retrieve_relevant(
    query="submit form",
    top_k=5,
    filters={"task": "form_submission"}
)

# Get statistics
stats = memory.get_stats()
print(f"Total episodes stored: {stats['total_episodes']}")
```

### 3. Memory Summarizer

The memory summarizer prevents prompt bloat by creating rolling summaries of agent history.

#### Features

- **Automatic summarization**: Summarizes history every N steps
- **Configurable retention**: Keep only recent items in full detail
- **Compressed history**: Older items are summarized to save context window space

#### Usage

```python
from digital_humain.memory.episodic import MemorySummarizer

# Initialize summarizer
summarizer = MemorySummarizer(
    max_history=10,      # Keep last 10 items in full detail
    summary_cadence=5    # Summarize every 5 steps
)

# Check if it's time to summarize
if summarizer.should_summarize():
    summary = summarizer.create_summary(agent_history)

# Get compressed history
compressed = summarizer.get_compressed_history(full_history)
```

## GUI Integration

The enhanced GUI includes controls for all memory features:

### Recording Controls

- **Start/Stop Recording**: Toggle recording of user actions
- **Demo Name**: Specify name for the recording
- **Replay Dropdown**: Select demonstration to replay
- **Replay Button**: Execute the demonstration
- **Dry Run Button**: Preview actions without executing
- **Delete Button**: Remove a demonstration
- **Refresh Button**: Update the list of demonstrations

### Memory Settings

- **Episodic Memory Toggle**: Enable/disable episodic recall
- **Speed Slider**: Adjust replay speed (0.5x to 2.0x)
- **Safety Pause Toggle**: Enable/disable 3-second safety delay before replay

### Agent Integration

When executing tasks, the agent:

1. **Retrieves** relevant past episodes (if episodic memory enabled)
2. **Executes** the task with enhanced context
3. **Stores** new episodes for future reference
4. **Logs** memory statistics

## Safety & Privacy

### Guardrails

- **Secret Detection**: Automatically filters episodes containing passwords, API keys, tokens, etc.
- **Confirmation Required**: Critical operations like clearing episodes require explicit confirmation
- **Who/When Tracking**: All memory operations track which agent made changes and when
- **Allowlist System**: Only allowed data types are persisted

### Safety Features

- **Dry Run Mode**: Preview actions before executing
- **Safety Pause**: 3-second delay before replay (can abort by moving mouse to corner)
- **Fail-safe**: PyAutoGUI fail-safe enabled (move to corner to abort)
- **Configurable Limits**: Maximum episode counts prevent unbounded growth

## Storage

All memory data is stored locally:

- **Demonstrations**: `./demonstrations/` (configurable)
- **Episodic Memory**: `./episodic_memory/` (configurable)
- **Format**: JSON files with human-readable structure

## Performance Considerations

- **Recording Overhead**: Mouse move events are sampled (every 10th event) to reduce noise
- **Retrieval Speed**: Simple keyword-based matching (can be enhanced with vector search)
- **Storage Growth**: Automatic pruning when max_episodes limit is reached
- **Memory Footprint**: Episodes are loaded on-demand from disk

## Future Enhancements

Potential improvements for future versions:

1. **Vector Search**: Use embeddings for semantic episode retrieval
2. **LLM-based Summarization**: Replace simple summarization with LLM-generated summaries
3. **UI Shift Adaptation**: Advanced heuristics to handle UI layout changes during replay
4. **Multi-step Planning**: Use episodic memory to plan complex multi-step tasks
5. **Collaborative Memory**: Share demonstrations and episodes across team members
6. **Visual Context**: Store screenshots alongside actions for better context matching

## Testing

Comprehensive unit tests cover:

- ✅ Recording and saving demonstrations
- ✅ Loading and replaying demonstrations
- ✅ Dry run mode
- ✅ Episode creation and retrieval
- ✅ Secret filtering and guardrails
- ✅ Memory summarization
- ✅ Persistence and reload
- ✅ Maximum episode limits

Run tests with:
```bash
python -m pytest tests/unit/test_memory.py -v
```

## Examples

See `examples/memory_demo.py` for complete working examples of all memory features.

```bash
python examples/memory_demo.py
```
