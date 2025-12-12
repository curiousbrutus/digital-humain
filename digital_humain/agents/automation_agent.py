"""Desktop automation agent implementation."""

from typing import Dict, Any
from loguru import logger

from digital_humain.core.agent import BaseAgent, AgentConfig, AgentState
from digital_humain.core.llm import LLMProvider
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry


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
        reasoning_lower = reasoning.lower()
        import re
        
        # Analyze screen if needed
        if any(word in reasoning_lower for word in ["analyze", "look", "check", "see"]):
            analysis = self.screen.analyze_screen(state['task'])
            return {
                "action": "analyze_screen",
                "success": analysis.get("success", False),
                "result": analysis
            }
        
        # Click action
        if "click" in reasoning_lower:
            # Try to find element mentioned in reasoning
            # This is simplified - real implementation would extract coordinates
            result = self.actions.click()
            return {
                "action": "click",
                "success": result.get("success", False),
                "result": result
            }
        
        # Type action
        if any(word in reasoning_lower for word in ["type", "enter", "input", "write"]):
            # Try to extract text to type (content in quotes)
            text_match = re.search(r'["\'](.*?)["\']', reasoning)
            if text_match:
                text_to_type = text_match.group(1)
            else:
                # Fallback to context or placeholder
                text_to_type = state['context'].get('input_text', 'placeholder text')
            
            result = self.actions.type_text(text_to_type)
            return {
                "action": "type_text",
                "success": result.get("success", False),
                "result": result,
                "text": text_to_type
            }
            
        # Press key action
        if any(word in reasoning_lower for word in ["press", "hit"]):
             # Extract key name
             key_match = re.search(r'(?:press|hit)\s+(?:the\s+)?(\w+)', reasoning_lower)
             if key_match:
                 key = key_match.group(1)
                 # Map common key names if needed
                 if key in ["enter", "return"]: key = "enter"
                 if key in ["windows", "super", "cmd"]: key = "win"
                 
                 result = self.actions.press_key(key)
                 return {
                     "action": "press_key",
                     "success": result.get("success", False),
                     "result": result,
                     "key": key
                 }

        # File operations
        if "read file" in reasoning_lower or "open file" in reasoning_lower:
            # Try to extract file path from context
            file_path = state['context'].get('file_path', './data/sample.txt')
            result = self.tools.execute("file_read", path=file_path)
            return {
                "action": "file_read",
                "success": result.get("success", False),
                "result": result,
                "path": file_path
            }
        
        # Wait action
        if "wait" in reasoning_lower:
            result = self.actions.wait(1.0)
            return {
                "action": "wait",
                "success": result.get("success", False),
                "result": result
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
