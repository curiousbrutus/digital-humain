"""Multi-agent orchestration example."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from digital_humain.core.agent import AgentConfig, AgentRole
from digital_humain.core.llm import OllamaProvider
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.file_tools import FileReadTool, FileWriteTool, FileListTool
from digital_humain.agents.automation_agent import DesktopAutomationAgent
from digital_humain.orchestration.coordinator import AgentCoordinator
from digital_humain.orchestration.registry import AgentRegistry
from digital_humain.orchestration.memory import SharedMemory
from digital_humain.utils.logger import setup_logger
from digital_humain.utils.config import load_config


def create_agent(
    name: str,
    role: AgentRole,
    llm: OllamaProvider,
    screen_analyzer: ScreenAnalyzer,
    gui_actions: GUIActions,
    tool_registry: ToolRegistry,
    config: dict
) -> DesktopAutomationAgent:
    """Create an agent with given configuration."""
    agent_config = AgentConfig(
        name=name,
        role=role,
        model=config.get("llm", {}).get("model", "llama2"),
        max_iterations=config.get("agents", {}).get("max_iterations", 10),
        verbose=config.get("agents", {}).get("verbose", True)
    )
    
    return DesktopAutomationAgent(
        config=agent_config,
        llm_provider=llm,
        screen_analyzer=screen_analyzer,
        gui_actions=gui_actions,
        tool_registry=tool_registry
    )


def main():
    """Run multi-agent orchestration example."""
    # Setup
    setup_logger(level="INFO")
    config = load_config()
    
    print("=" * 60)
    print("Digital Humain - Multi-Agent Orchestration Example")
    print("=" * 60)
    
    # Initialize shared components
    print("\n[1/5] Initializing shared components...")
    llm = OllamaProvider(
        model=config.get("llm", {}).get("model", "llama2"),
        base_url=config.get("llm", {}).get("base_url", "http://localhost:11434")
    )
    
    screen_analyzer = ScreenAnalyzer(
        save_screenshots=config.get("vlm", {}).get("save_screenshots", True),
        screenshot_dir=config.get("vlm", {}).get("screenshot_dir", "./screenshots")
    )
    
    gui_actions = GUIActions(
        pause=config.get("agents", {}).get("pause", 0.5),
        safe_mode=config.get("agents", {}).get("safe_mode", True)
    )
    
    tool_registry = ToolRegistry()
    tool_registry.register(FileReadTool())
    tool_registry.register(FileWriteTool())
    tool_registry.register(FileListTool())
    
    print("✓ Shared components initialized")
    
    # Create multiple agents
    print("\n[2/5] Creating agents...")
    
    planner_agent = create_agent(
        "planner",
        AgentRole.PLANNER,
        llm,
        screen_analyzer,
        gui_actions,
        tool_registry,
        config
    )
    print("✓ Planner agent created")
    
    executor_agent = create_agent(
        "executor",
        AgentRole.EXECUTOR,
        llm,
        screen_analyzer,
        gui_actions,
        tool_registry,
        config
    )
    print("✓ Executor agent created")
    
    analyzer_agent = create_agent(
        "analyzer",
        AgentRole.ANALYZER,
        llm,
        screen_analyzer,
        gui_actions,
        tool_registry,
        config
    )
    print("✓ Analyzer agent created")
    
    # Setup orchestration
    print("\n[3/5] Setting up orchestration...")
    registry = AgentRegistry()
    memory = SharedMemory()
    coordinator = AgentCoordinator(registry=registry, memory=memory)
    
    # Register agents
    coordinator.register_agent(planner_agent)
    coordinator.register_agent(executor_agent)
    coordinator.register_agent(analyzer_agent)
    
    print(f"✓ Orchestration ready with {len(registry.list_agents())} agents")
    
    # Show agent info
    print("\n[4/5] Agent registry:")
    for agent_info in registry.list_agents_info():
        print(f"  - {agent_info['name']} ({agent_info['role']})")
    
    # Execute complex task
    print("\n[5/5] Executing complex task...")
    print("-" * 60)
    
    task = "Analyze the accounting software, plan data entry steps, and execute the workflow"
    print(f"Task: {task}")
    print("-" * 60)
    
    try:
        result = coordinator.execute_task(task)
        
        print("\n" + "=" * 60)
        print("ORCHESTRATION RESULTS")
        print("=" * 60)
        print(f"Status: {'✓ Success' if result['success'] else '✗ Failed'}")
        print(f"Subtasks: {result['subtasks']}")
        print(f"Total steps: {result['total_steps']}")
        
        print("\nSubtask Results:")
        for i, subtask_result in enumerate(result['results'], 1):
            print(f"\n  [{i}] {subtask_result['subtask']['description']}")
            print(f"      Agent: {subtask_result.get('agent', 'none')}")
            print(f"      Status: {'✓' if subtask_result.get('success') else '✗'}")
            print(f"      Steps: {subtask_result.get('steps', 0)}")
        
        # Show shared memory
        print("\n" + "=" * 60)
        print("SHARED MEMORY")
        print("=" * 60)
        memory_stats = memory.stats()
        print(f"Total keys: {memory_stats['total_keys']}")
        print(f"History entries: {memory_stats['history_entries']}")
        
    except Exception as e:
        print(f"\n✗ Execution failed: {e}")
        print("\nNote: Make sure Ollama is running with: ollama serve")
        print("And that you have pulled a model: ollama pull llama2")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
