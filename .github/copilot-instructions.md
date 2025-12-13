# GitHub Copilot Instructions for Digital Humain

## Project Overview

Digital Humain is a self-hosted Python-based agentic AI framework for enterprise desktop automation. It combines LangGraph-based orchestration with Vision Language Models (VLM) for GUI interaction, providing a privacy-first solution for automating desktop applications with local LLM inference.

## Architecture

The project follows a modular architecture with clear separation of concerns:

```
digital_humain/
├── core/               # Core agent framework (ReAct pattern)
├── vlm/               # Vision Language Model for screen analysis
├── memory/            # Learning and recall systems
├── orchestration/     # Multi-agent coordination
├── tools/             # Tool execution framework
├── agents/            # Concrete agent implementations
└── utils/             # Utilities and configuration
```

## Key Technologies

- **Agent Framework**: LangGraph for orchestration, LangChain for LLM integration
- **LLM Providers**: Ollama (local), OpenRouter, Letta (self-hosted)
- **Vision**: OpenCV, Pillow, PyTesseract for screen analysis and OCR
- **GUI Automation**: PyAutoGUI, PyWinAuto (Windows), python-xlib (Linux)
- **Data Validation**: Pydantic v2
- **Configuration**: YAML files in `config/` directory
- **Logging**: Loguru for structured logging

## Development Environment

### Prerequisites
- Python 3.9+
- Ollama (for local LLM inference)
- Platform-specific GUI automation libraries

### Setup
```bash
pip install -r requirements.txt
# For development:
pip install -e .[dev]
```

### Testing
```bash
pytest tests/
pytest tests/unit/
pytest tests/integration/
```

## Code Style & Conventions

### Python Style
- Follow PEP 8 conventions
- Use type hints for function signatures
- Maximum line length: 100 characters (as commonly used in modern Python projects)
- Use `black` for code formatting
- Use `flake8` for linting
- Use `mypy` for type checking

### Code Organization
- **Agents**: Implement `BaseAgent` from `digital_humain.core.agent`
- **Tools**: Extend `BaseTool` from `digital_humain.tools.base`
- **Configuration**: Use Pydantic models for config validation
- **Error Handling**: Use appropriate exception handling with informative messages
- **Logging**: Use `loguru` logger consistently across modules

### Naming Conventions
- Classes: `PascalCase` (e.g., `DesktopAutomationAgent`)
- Functions/Methods: `snake_case` (e.g., `analyze_screen`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_ITERATIONS`)
- Private members: Prefix with `_` (e.g., `_internal_method`)

### Documentation
- Use docstrings for classes and public methods (Google style)
- Include type hints in function signatures
- Document complex algorithms with inline comments
- Update README.md for major feature additions

## Core Patterns

### Agent Pattern (ReAct)
Agents follow the Reasoning + Acting pattern:
1. **Observe**: Analyze current state
2. **Reason**: Determine next action using LLM
3. **Act**: Execute the action
4. **Repeat**: Continue until task complete

Example:
```python
class MyAgent(BaseAgent):
    def reason(self, state, observation):
        # Use LLM to determine next action
        pass
    
    def act(self, state, reasoning):
        # Execute the determined action
        pass
```

### Tool Development
Tools must implement the `BaseTool` interface:
```python
class MyTool(BaseTool):
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="tool_name",
            description="Clear description of what the tool does",
            parameters=[...]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        # Implementation
        pass
```

### Memory System
- **Episodic Memory**: Store and retrieve past experiences
- **Demonstration Recording**: Learn from user actions
- **Memory Summarization**: Prevent prompt bloat in long-running tasks

## Testing Practices

### Unit Tests
- Located in `tests/unit/`
- Test individual components in isolation
- Mock external dependencies (LLMs, file system, GUI)
- Use pytest fixtures for common setup

### Integration Tests
- Located in `tests/integration/`
- Test component interactions
- May require Ollama or mock LLM providers

### Test Naming
- Format: `test_<function_name>_<scenario>_<expected_result>`
- Example: `test_agent_execute_with_invalid_input_raises_error`

## Security & Privacy

- **No External API Calls**: Default to local Ollama for LLM inference
- **Environment Variables**: Use `.env` for API keys (never commit)
- **Data Privacy**: All processing happens locally by default
- **Input Validation**: Use Pydantic for structured inputs (configuration, API parameters, agent inputs, tool parameters)

## Configuration

### Config Files
- `config/config.yaml`: Main application configuration
- `.env`: API keys and secrets (gitignored)

### Environment Variables
- `OPENROUTER_API_KEY`: OpenRouter API key
- `LETTA_API_KEY`: Letta API key
- `LETTA_AGENT_ID`: Letta agent identifier

## Common Development Tasks

### Adding a New Agent
1. Create class extending `BaseAgent` in `digital_humain/agents/`
2. Implement `reason()` and `act()` methods
3. Register in `AgentRegistry` if used with orchestration
4. Add unit tests in `tests/unit/`
5. Update documentation

### Adding a New Tool
1. Create class extending `BaseTool` in `digital_humain/tools/`
2. Implement `get_metadata()` and `execute()` methods
3. Register in `ToolRegistry` where used
4. Add unit tests with mocked dependencies
5. Document parameters and return values

### Modifying VLM Capabilities
1. Update screen analysis in `digital_humain/vlm/screen_analyzer.py`
2. Update GUI actions in `digital_humain/vlm/actions.py`
3. Test with actual screen captures
4. Consider platform-specific behavior (Windows/Linux/Mac)

## GUI Applications

### GUI App (`gui_app.py`)
- Tkinter-based desktop application
- Includes LLM configuration, task execution, and recording controls
- Test manually with: `python gui_app.py`

### Web App (`web_app.py`)
- Web-based interface for remote access
- Test manually with: `python web_app.py`

### Building Executable
```bash
python build_exe.py
```
Creates standalone Windows executable in `dist/`

## Dependencies Management

### Adding Dependencies
1. Add to `requirements.txt` with version constraints
2. Update `setup.py` if it's a core dependency
3. Document in README.md if it requires special setup
4. Consider platform-specific dependencies (use markers)

### Platform-Specific Dependencies
```
pywinauto>=0.6.8; platform_system=="Windows"
python-xlib>=0.33; platform_system=="Linux"
pyobjc-framework-Quartz>=9.0; platform_system=="Darwin"
```

## Error Handling

### Common Patterns
```python
from loguru import logger

try:
    # Operation
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise CustomException("User-friendly message") from e
```

### LLM Provider Errors
- Handle connection timeouts gracefully
- Provide fallback behavior when LLM unavailable
- Log LLM requests/responses for debugging

### GUI Automation Errors
- Element not found: Retry with timeout
- Screen capture failures: Log and continue
- Platform-specific exceptions: Handle per-platform

## Performance Considerations

- **Screen Captures**: Optimize resolution and frequency
- **LLM Calls**: Cache responses when appropriate
- **Memory Management**: Summarize long conversation histories
- **Tool Execution**: Implement timeouts for long-running tools

## Debugging

### Logging
- Use `logger.debug()` for detailed execution flow
- Use `logger.info()` for major steps
- Use `logger.warning()` for recoverable issues
- Use `logger.error()` for failures

### Common Debug Points
- Screen analyzer: Save captured images to `screenshots/`
- LLM responses: Log prompts and completions
- Agent reasoning: Log observation → reasoning → action flow
- Tool execution: Log parameters and results

## Contributing Guidelines

1. Create feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass: `pytest tests/`
4. Run linters: `black .` and `flake8 .`
5. Update documentation
6. Submit pull request with clear description

## Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph/)
- [Ollama Documentation](https://ollama.ai/docs)
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)
- [Project Documentation](docs/README.md)
