"""Simple desktop automation example."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from digital_humain.core.agent import AgentConfig, AgentRole
from digital_humain.core.llm import OllamaProvider
from digital_humain.core.engine import AgentEngine
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.file_tools import FileReadTool, FileWriteTool, FileListTool
from digital_humain.agents.automation_agent import DesktopAutomationAgent
from digital_humain.utils.logger import setup_logger
from digital_humain.utils.config import load_config


def main():
    """Run a simple desktop automation task."""
    # Setup
    setup_logger(level="INFO")
    config = load_config()
    
    print("=" * 60)
    print("Digital Humain - Desktop Automation Example")
    print("=" * 60)
    
    # Initialize LLM provider
    print("\n[1/6] Initializing LLM provider...")
    llm_config = config.get("llm", {})
    llm = OllamaProvider(
        model=llm_config.get("model", "llama2"),
        base_url=llm_config.get("base_url", "http://localhost:11434"),
        timeout=llm_config.get("timeout", 60)
    )
    print(f"✓ LLM provider initialized: {llm_config.get('model', 'llama2')}")
    
    # Initialize VLM components
    print("\n[2/6] Initializing VLM components...")
    vlm_config = config.get("vlm", {})
    screen_analyzer = ScreenAnalyzer(
        vlm_provider=None,  # Can add VLM later
        save_screenshots=vlm_config.get("save_screenshots", True),
        screenshot_dir=vlm_config.get("screenshot_dir", "./screenshots")
    )
    gui_actions = GUIActions(
        pause=config.get("agents", {}).get("pause", 0.5),
        safe_mode=config.get("agents", {}).get("safe_mode", True)
    )
    print("✓ VLM components initialized")
    
    # Initialize tool registry
    print("\n[3/6] Initializing tool registry...")
    tool_registry = ToolRegistry()
    tool_registry.register(FileReadTool())
    tool_registry.register(FileWriteTool())
    tool_registry.register(FileListTool())
    print(f"✓ Tool registry initialized with {len(tool_registry.list_tools())} tools")
    
    # Create agent
    print("\n[4/6] Creating desktop automation agent...")
    agent_config = AgentConfig(
        name="desktop_agent",
        role=AgentRole.EXECUTOR,
        model=llm_config.get("model", "llama2"),
        max_iterations=config.get("agents", {}).get("max_iterations", 10),
        verbose=config.get("agents", {}).get("verbose", True)
    )
    
    agent = DesktopAutomationAgent(
        config=agent_config,
        llm_provider=llm,
        screen_analyzer=screen_analyzer,
        gui_actions=gui_actions,
        tool_registry=tool_registry
    )
    print(f"✓ Agent created: {agent_config.name}")
    
    # Create engine
    print("\n[5/6] Creating agent execution engine...")
    engine = AgentEngine(agent)
    engine.build_graph()
    print("✓ Execution engine ready")
    
    # Run a simple task
    print("\n[6/6] Executing task...")
    print("-" * 60)
    
    task = "Analyze the current screen and identify key elements"
    print(f"Task: {task}")
    print("-" * 60)
    
    # Note: This will fail gracefully if Ollama is not running
    try:
        result = engine.run(task)
        
        print("\n" + "=" * 60)
        print("EXECUTION RESULTS")
        print("=" * 60)
        print(f"Status: {'✓ Success' if not result['error'] else '✗ Error'}")
        print(f"Steps completed: {result['current_step']}")
        print(f"Actions taken: {len(result['actions'])}")
        
        if result['error']:
            print(f"Error: {result['error']}")
        
        if result['result']:
            print(f"\nResult: {result['result']}")
        
    except Exception as e:
        print(f"\n✗ Execution failed: {e}")
        print("\nNote: Make sure Ollama is running with: ollama serve")
        print("And that you have pulled a model: ollama pull llama2")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
