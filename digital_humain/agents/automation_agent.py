"""Desktop automation agent implementation."""

from typing import Dict, Any
import subprocess
from loguru import logger

from digital_humain.core.agent import BaseAgent, AgentConfig, AgentState
from digital_humain.core.llm import LLMProvider
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.agents.action_parser import ActionParser, AppLauncher


class DesktopAutomationAgent(BaseAgent):
    """
    Agent specialized in desktop automation tasks.
    
    Combines VLM for screen understanding with action execution
    for enterprise desktop automation (HBYS, Accounting, Quality).
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm_provider: LLMProvider,
        screen_analyzer: ScreenAnalyzer,
        gui_actions: GUIActions,
        tool_registry: ToolRegistry
    ):
        """
        Initialize the desktop automation agent.
        
        Args:
            config: Agent configuration
            llm_provider: LLM provider for reasoning
            screen_analyzer: Screen analyzer for VLM
            gui_actions: GUI action executor
            tool_registry: Tool registry for file operations
        """
        super().__init__(config)
        self.llm = llm_provider
        self.screen = screen_analyzer
        self.actions = gui_actions
        self.tools = tool_registry
        logger.info(f"Initialized DesktopAutomationAgent: {config.name}")
    
    def reason(self, state: AgentState, observation: str) -> str:
        """
        Reason about next action using LLM.
        
        Args:
            state: Current agent state
            observation: Current observation
            
        Returns:
            Reasoning explanation
        """
        # Build reasoning prompt
        prompt = f"""Current Task: {state['task']}

Observation:
{observation}

Previous Actions:
{self._format_history(state)}

Based on the current situation, what should be the next action to complete the task?
Think step-by-step and explain your reasoning.

Reasoning:"""
        
        try:
            reasoning = self.llm.generate_sync(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
                temperature=self.config.temperature,
                max_tokens=500
            )
            return reasoning.strip()
        
        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            return f"Error in reasoning: {e}"
    
    def act(self, state: AgentState, reasoning: str) -> Dict[str, Any]:
        """
        Execute action based on reasoning.
        
        Args:
            state: Current agent state
            reasoning: Reasoning from previous step
            
        Returns:
            Action result dictionary
        """
        # Determine action from reasoning
        action_result = self._parse_and_execute_action(reasoning, state)
        
        # Check if task is complete
        if self._is_task_complete(state, action_result):
            state['result'] = {
                "status": "completed",
                "actions_taken": len(state['actions']),
                "final_observation": state['observations'][-1] if state['observations'] else None
            }
        
        return action_result
    
    def _format_history(self, state: AgentState) -> str:
        """Format action history for prompt."""
        if not state['history']:
            return "None"
        
        # Show last 3 actions
        recent = state['history'][-3:]
        formatted = []
        
        for entry in recent:
            action = entry.get('action', {})
            formatted.append(
                f"Step {entry['step']}: {action.get('action', 'unknown')} - "
                f"Success: {action.get('success', False)}"
            )
        
        return "\n".join(formatted)
    
    def _parse_and_execute_action(
        self,
        reasoning: str,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Parse reasoning and execute appropriate action.
        
        Args:
            reasoning: Reasoning text
            state: Current state
            
        Returns:
            Action result
        """
        # Parse intent using new ActionParser
        intent = ActionParser.parse(reasoning, state.get('context'), state.get('task'))
        
        logger.info(f"[Action Parser] {intent}")
        
        # Handle no_action case
        if intent.action_type == "no_action":
            return {
                "action": "no_action",
                "success": True,
                "reason": intent.reason,
                "result": "No actionable command detected"
            }
        
        # Handle task completion
        if intent.action_type == "task_complete":
            return {
                "action": "task_complete",
                "success": True,
                "result": "Task marked as complete by agent"
            }
        
        # Launch app
        if intent.action_type == "launch_app":
            app_name = intent.params.get("app_name", "")
            result = AppLauncher.launch_app(app_name)
            if result.get("success"):
                self.actions.wait(0.5)  # Brief wait for app to start
            return result
        
        # Press key
        if intent.action_type == "press_key":
            key = intent.params.get("key", "")
            result = self.actions.press_key(key)
            logger.info(f"[Press Key] {key} -> Success: {result.get('success', False)}")
            return {
                "action": "press_key",
                "success": result.get("success", False),
                "result": result,
                "key": key
            }
        
        # Type text
        if intent.action_type == "type_text":
            text_to_type = intent.params.get("text", "")
            result = self.actions.type_text(text_to_type)
            logger.info(f"[Type Text] '{text_to_type[:50]}...' -> Success: {result.get('success', False)}")
            return {
                "action": "type_text",
                "success": result.get("success", False),
                "result": result,
                "text": text_to_type
            }
        
        # Click
        if intent.action_type == "click":
            x = intent.params.get("x")
            y = intent.params.get("y")
            result = self.actions.click(x, y)
            logger.info(f"[Click] ({x}, {y}) -> Success: {result.get('success', False)}")
            return {
                "action": "click",
                "success": result.get("success", False),
                "result": result,
                "position": (x, y) if x and y else None
            }
        
        # Analyze screen
        if intent.action_type == "analyze_screen":
            analysis = self.screen.analyze_screen(state['task'])
            logger.info(f"[Analyze Screen] Success: {analysis.get('success', False)}")
            return {
                "action": "analyze_screen",
                "success": analysis.get("success", False),
                "result": analysis
            }
        
        # Wait
        if intent.action_type == "wait":
            duration = intent.params.get("duration", 1.0)
            result = self.actions.wait(duration)
            return {
                "action": "wait",
                "success": result.get("success", False),
                "result": result,
                "duration": duration
            }
        
        # File operations
        if intent.action_type == "file_read":
            file_path = state.get('context', {}).get('file_path', './data/sample.txt')
            result = self.tools.execute("file_read", path=file_path)
            return {
                "action": "file_read",
                "success": result.get("success", False),
                "result": result,
                "path": file_path
            }
        
        # Default: continue observation
        return {
            "action": "observe",
            "success": True,
            "result": "Continuing observation"
        }
    
    def _is_task_complete(self, state: AgentState, action_result: Dict[str, Any]) -> bool:
        """
        Determine if task is complete.
        
        Args:
            state: Current state
            action_result: Latest action result
            
        Returns:
            True if task is complete
        """
        # Check if reasoning indicates completion
        if state['reasoning']:
            last_reasoning = state['reasoning'][-1].lower()
            if any(word in last_reasoning for word in ["complete", "done", "finish", "success"]):
                return True
        
        # Check max steps
        if state['current_step'] >= state['max_steps'] - 1:
            return True
        
        return False
