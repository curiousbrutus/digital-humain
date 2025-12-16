# Letta-Style GUI Documentation

## Overview

The enhanced Letta-style GUI provides a professional, feature-rich interface for Desktop Automation with memory management, conversation tracking, and visual feedback inspired by Letta (formerly MemGPT).

## Key Features

### 1. **Core Memory Management**
Letta-style memory blocks for persistent context:

#### Human Block (2000 chars max)
- Stores information about the user
- Name, preferences, context
- Automatically tracked across sessions
- Real-time character counter
- Editable in-place

#### Persona Block (2000 chars max)
- Defines agent personality and capabilities
- Agent behavior guidelines
- Skills and knowledge base
- Customizable identity

**Usage:**
```python
core_memory = CoreMemory()
core_memory.set_human("Name: Sarah, Role: Medical Staff, Uses Bizmed")
core_memory.set_persona("I am a medical workflow automation assistant...")
```

### 2. **Archival Memory**
Long-term storage for experiences and knowledge:

- **Add memories**: Store important information permanently
- **Search**: Keyword-based retrieval
- **View/Delete**: Manage stored memories
- **Persistent**: Survives app restarts (JSON storage)
- **Unlimited capacity**: No hard limits

**Usage:**
```python
archival_memory.add("Completed patient data entry workflow successfully")
results = archival_memory.search("patient data")
```

### 3. **Conversation Management**

#### Agent Simulator
- **Rich conversation display** with timestamps
- **User/Agent role indicators** (👤/🤖)
- **Reasoning display**: Shows agent's internal thought process
- **Auto-advance mode**: Automatic conversation flow
- **Voice input**: Speech-to-text support
- **Message history**: Full conversation tracking

#### Features:
- Color-coded messages (blue for user, green for agent)
- Italic reasoning display
- Scrollable history
- Copy/paste support
- Clear conversation

### 4. **Context Window Management**

#### Token Tracking
- **Real-time token count**: Shows `current/max` tokens
- **Visual progress bar**: Color-coded by usage
  - Green: < 70% usage
  - Orange: 70-90% usage
  - Red: > 90% usage
- **Automatic updates**: Tracks conversation length

### 5. **Three-Panel Layout**

#### Left Panel: Agent Settings (300px)
- LLM Configuration
  - Provider selection (Ollama/OpenRouter/Letta)
  - Health indicator (colored dot)
  - Model selection with filtering
  - API key management
- Agent Configuration
  - Agent type selection
  - Frequency control
  - System instructions editor
- Tools (collapsible)

#### Center Panel: Main Workspace
- **Agent Simulator Tab**: Conversation interface
- **Execution Logs Tab**: Detailed logging
- **Memory Management Tab**: Demo recording/replay

#### Right Panel: Context Window (350px)
- Token count display
- Core Memory blocks
  - Human context
  - Persona definition
- Archival Memory
  - Search interface
  - Memory list
  - CRUD operations

### 6. **Enhanced Visual Design**

#### Color Scheme (Letta-inspired)
- Deep dark background (`#0f111a`)
- Panel backgrounds (`#1a1d2e`, `#252837`)
- Indigo accent (`#6366f1`)
- Semantic colors:
  - Success: `#10b981` (green)
  - Warning: `#f59e0b` (orange)
  - Error: `#ef4444` (red)

#### Typography
- Headers: Segoe UI, Bold, 11pt
- Body: Segoe UI, 9-10pt
- Code/Logs: Consolas, 9pt
- Accessible contrast ratios

### 7. **Memory Systems Integration**

#### Demonstration Recording
- Record user actions for replay
- Name and save demonstrations
- Replay with speed control (0.5x - 2x)
- Dry run mode (preview without execution)
- Delete unwanted demos

#### Episodic Memory
- Toggle on/off
- Automatic experience tracking
- Retrieval for similar situations

#### Visual Indicators
- Real-time overlay showing agent actions
- Toggle on/off
- See clicks, typing, and navigation

## Usage Guide

### Starting the Application

```bash
python gui_app_letta.py
```

### Initial Setup

1. **Select Provider**
   - Auto-detects Ollama if installed
   - Falls back to OpenRouter with API key
   - Health indicator shows status

2. **Configure Core Memory**
   - Edit Human block with user context
   - Customize Persona for agent behavior
   - Save changes (💾 button)

3. **Start Conversation**
   - Type message in input area
   - Click "▶ Send" or press Enter
   - Agent responds with reasoning

### Working with Memory

#### Adding Archival Memory
1. Go to "Archival Memory" tab
2. Click "+ Add" button
3. Enter content in dialog
4. Click "Save"

#### Searching Memories
1. Enter search query in search box
2. Click "🔍 Search"
3. Results appear in list
4. Click memory to view details

#### Recording Demonstrations
1. Go to "Memory Management" tab
2. Enter demo name
3. Click "⏺ Start Recording"
4. Perform actions on screen
5. Click "⏹ Stop Recording"
6. Demo is saved automatically

#### Replaying Demonstrations
1. Select demo from dropdown
2. Adjust speed slider (0.5x - 2x)
3. Click "▶ Replay"
4. Watch automation execute

### Conversation Best Practices

1. **Provide Context**: Update Human block with relevant info
2. **Clear Persona**: Define agent capabilities and boundaries
3. **Use Reasoning**: Review agent's thought process
4. **Archive Important Info**: Store learnings in Archival Memory
5. **Monitor Tokens**: Keep conversation under context limit

## Architecture

### Class Structure

```python
CoreMemory
├── human: str (max 2000 chars)
├── persona: str (max 2000 chars)
├── get_human() -> str
├── set_human(content) -> bool
├── get_persona() -> str
└── set_persona(content) -> bool

ArchivalMemory
├── memories: List[Dict]
├── add(content, metadata)
├── search(query, limit) -> List[Dict]
├── get_all() -> List[Dict]
└── delete(memory_id) -> bool

ConversationMessage
├── role: str ("user" | "agent")
├── content: str
├── timestamp: datetime
├── internal_reasoning: str
└── to_dict() -> Dict

LettaStyleGUI
├── core_memory: CoreMemory
├── archival_memory: ArchivalMemory
├── conversation: List[ConversationMessage]
├── setup_ui()
├── add_message(role, content, reasoning)
├── send_message()
└── run_conversation()
```

### Data Storage

- **Core Memory**: In-memory (session-based)
- **Archival Memory**: `memory/archival/archival.json`
- **Demonstrations**: `memory/demonstrations/*.json`
- **Episodic Memory**: `memory/episodic/episodes.json`

## Keyboard Shortcuts

- **Ctrl+Enter** (in input): Send message
- **Ctrl+L**: Clear conversation
- **Ctrl+R**: Refresh models
- **Ctrl+S** (in memory blocks): Save changes

## Configuration

### System Instructions
Default system instructions can be edited in the "System Instructions" panel. These guide the agent's behavior.

Example:
```
Act as a desktop automation agent. Help users automate tasks using vision and reasoning.
- Be proactive in understanding user intent
- Use screen analysis before taking actions
- Confirm destructive operations
- Learn from user demonstrations
- Store important discoveries in archival memory
```

### Agent Types
- `desktop_automation`: Standard desktop automation agent
- `memgpt_agent`: Memory-augmented agent with enhanced recall

### Frequency
Controls how often the agent checks for updates (1-10 scale).

## Comparison with Original GUI

| Feature | Original GUI | Letta-Style GUI |
|---------|-------------|-----------------|
| Layout | Single column | Three-panel professional |
| Memory | Basic episodic | Core + Archival + Episodic |
| Conversation | Logs only | Rich conversation display |
| Token Tracking | None | Real-time with visual bar |
| Character Limits | None | Enforced with counters |
| Reasoning Display | Hidden | Visible italic text |
| Visual Design | Functional | Professional Letta-inspired |
| Context Management | Manual | Structured blocks |

## Advanced Features

### Auto-Advance Mode
When enabled, agent automatically processes responses without requiring "Send" clicks.

### Voice Input
Click 🎤 button to use speech-to-text for message input (requires `speech_recognition` package).

### Memory Export/Import
(Future feature) Export/import memory state for backup or transfer.

### Multi-Agent Support
(Future feature) Multiple agent personas with separate memory blocks.

## Troubleshooting

### Memory Not Saving
- Check `memory/` directory exists
- Verify write permissions
- Check disk space

### Token Count Inaccurate
- Token count is estimated (words × 1.3)
- For exact count, use provider's tokenizer
- Future: Integrate tiktoken for accuracy

### Core Memory Exceeds Limit
- Red character counter indicates overflow
- Edit content to fit within limit
- Use archival memory for overflow

### Archival Search Not Working
- Search is case-insensitive keyword match
- Use specific terms
- Future: Semantic search with embeddings

## Performance Notes

- **Startup time**: ~2-3 seconds
- **Memory search**: O(n) linear scan (fast for <10k memories)
- **Token tracking**: Minimal overhead
- **UI responsiveness**: Non-blocking threading

## Future Enhancements

- [ ] Semantic archival search with embeddings
- [ ] Token count using tiktoken
- [ ] Memory visualization (graph view)
- [ ] Multi-agent workspace
- [ ] Memory export/import (JSON/CSV)
- [ ] Conversation bookmarks
- [ ] Custom memory block types
- [ ] Memory compression for long contexts
- [ ] Cloud sync for memories
- [ ] Keyboard shortcut customization

## Related Documentation

- [Original GUI](../gui_app.py)
- [Core Memory Implementation](../digital_humain/memory/)
- [Agent Architecture](ARCHITECTURE.md)
- [Visual Overlay](VISUAL_OVERLAY.md)

## Credits

Interface design inspired by [Letta (formerly MemGPT)](https://www.letta.com/) - an open-source memory-augmented LLM framework.
