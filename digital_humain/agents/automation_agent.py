"""Desktop automation agent implementation."""

from typing import Dict, Any
import subprocess
from loguru import logger

from digital_humain.core.agent import BaseAgent, AgentConfig, AgentState
from digital_humain.core.llm import LLMProvider
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.agents.action_parser import ActionParser, AppLauncher, ActionIntent


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
        history = self._format_history(state)
        
        # Determine what the next logical step is based on history
        next_step_hint = ""
        if history == "None":
            next_step_hint = "This is the first step. You should start by opening the required application."
        elif "launch_app" in history and "type_text" not in history:
            next_step_hint = "The app is now open. You should proceed to type the required content."
        elif "type_text" in history:
            # If the task includes saving/exporting, do not stop after typing.
            task_lower = (state.get('task') or "").lower()
            if any(k in task_lower for k in ["save", "export", "download"]):
                next_step_hint = (
                    "Text has been typed. If the task requires saving/exporting, perform that next "
                    "(e.g., use Ctrl+S / Save As and choose the requested location), then only mark task complete."
                )
            else:
                next_step_hint = "Text has been typed. If all requirements are satisfied, mark task complete."
        
        prompt = f"""Current Task: {state['task']}

Observation:
{observation}

Previous Actions:
{history}

{next_step_hint}

What is the NEXT action to complete the task? 
You MUST respond with your reasoning and clearly state your action.

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
        
        # Show last 3 actions with details
        recent = state['history'][-3:]
        formatted = []
        
        for entry in recent:
            action = entry.get('action', {})
            action_type = action.get('action', 'unknown')
            success = action.get('success', False)
            
            # Add action-specific details
            details = ""
            if action_type == "launch_app":
                details = f" (app: {action.get('app_name', 'unknown')})"
            elif action_type == "type_text":
                text = action.get('text', '')
                details = f" (typed: '{text[:30]}...')" if len(text) > 30 else f" (typed: '{text}')"
            elif action_type == "press_key":
                details = f" (key: {action.get('key', 'unknown')})"
            elif action_type == "click":
                x, y = action.get('x', '?'), action.get('y', '?')
                details = f" (at: {x}, {y})"
            
            formatted.append(
                f"Step {entry['step']}: {action_type}{details} - Success: {success}"
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
        
        # Handle no_action case - check if we should auto-advance based on history
        if intent.action_type == "no_action":
            # Check if model returned empty but we should advance to next step
            history = state.get('history', [])
            task = state.get('task', '')
            
            # If we just launched an app and haven't typed yet, auto-type based on task
            if history:
                last_action = history[-1].get('action', {})
                last_action_type = last_action.get('action', '')
                
                # After launching app, check if we need to type something
                if last_action_type == 'launch_app' and last_action.get('success'):
                    # Generate typing intent from task
                    typing_intent = ActionParser.parse_typing_intent(
                        "Type the content based on task", 
                        state.get('context'), 
                        task
                    )
                    if typing_intent.action_type == "type_text" and typing_intent.params.get('text'):
                        logger.info(f"[Auto-advance] Model returned empty, auto-typing based on task")
                        intent = typing_intent
                
                # If we already typed and model is silent, DO NOT auto-complete.
                # Many tasks include additional steps (save/export, navigation, verification).
                elif last_action_type == 'type_text' and last_action.get('success'):
                    task_lower = (task or "").lower()
                    if any(k in task_lower for k in ["save", "export", "download"]):
                        # Nudge progress with a safe, common shortcut.
                        logger.info("[Auto-advance] Text typed and task implies saving; sending Ctrl+S")
                        intent = ActionIntent(
                            action_type="hotkey",
                            confidence=0.7,
                            params={"keys": ["ctrl", "s"]},
                            reason="Heuristic: task contains save/export/download",
                        )
                    else:
                        logger.info("[Auto-advance] Model silent after typing; continuing with screen analysis")
            
            # If still no_action, do screen analysis (but limit consecutive analyses)
            if intent.action_type == "no_action":
                # Count consecutive analyze_screen actions
                consecutive_analyses = 0
                for h in reversed(history):
                    if h.get('action', {}).get('action') == 'analyze_screen':
                        consecutive_analyses += 1
                    else:
                        break
                
                # If too many consecutive analyses, force completion or error
                if consecutive_analyses >= 3:
                    logger.warning("[Auto-advance] Too many consecutive screen analyses, forcing completion")
                    return {
                        "action": "task_complete",
                        "success": True,
                        "result": "Task force-completed due to model not responding"
                    }
                
                analysis = self.screen.analyze_screen(task)
                return {
                    "action": "analyze_screen",
                    "success": analysis.get("success", False),
                    "result": analysis,
                    "reason": intent.reason
                }
        
        # Handle task completion
        if intent.action_type == "task_complete":
            return {
                "action": "task_complete",
                "success": True,
                "result": "Task marked as complete by agent"
            }

        # Hotkey (e.g., ctrl+s)
        if intent.action_type == "hotkey":
            keys = intent.params.get("keys") or []
            if not isinstance(keys, list) or len(keys) < 2:
                return {
                    "action": "hotkey",
                    "success": False,
                    "error": "Invalid hotkey keys",
                    "keys": keys,
                }
            result = self.actions.hotkey(*keys)
            logger.info(f"[Hotkey] {'+'.join(keys)} -> Success: {result.get('success', False)}")
            return {
                "action": "hotkey",
                "success": result.get("success", False),
                "result": result,
                "keys": keys,
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
        # Only end when the agent explicitly issues a completion action.
        # (This avoids false positives like "successfully typed".)
        if action_result.get("action") == "task_complete" and action_result.get("success"):
            return True
        
        # Check max steps
        if state['current_step'] >= state['max_steps'] - 1:
            return True
        
        return False
