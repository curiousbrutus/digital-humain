"""Enhanced agent execution engine with robust error handling and recovery."""

from typing import Any, Dict, List, Optional, Callable
import threading
from langgraph.graph import StateGraph, END
from loguru import logger

from digital_humain.core.agent import AgentState, BaseAgent
from digital_humain.core.exceptions import ToolException, ActionException
from digital_humain.utils.retry import RetryManager, is_transient_error


class EnhancedAgentEngine:
    """
    Enhanced agent execution engine with production-grade error handling.
    
    Features:
    - Explicit ToolException handling with recovery nodes
    - Exponential backoff for transient errors
    - State verification after critical actions
    - Deterministic error routing in the graph
    
    This implementation follows the recommendations from Section III.2:
    "Code Patterns for Guaranteed Error Recovery and Loop Prevention"
    """
    
    def __init__(
        self,
        agent: BaseAgent,
        cancel_event: Optional[threading.Event] = None,
        enable_recovery: bool = True,
        enable_verification: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize the enhanced engine.
        
        Args:
            agent: Agent instance to execute
            cancel_event: Optional cancellation event
            enable_recovery: Enable recovery node for error handling
            enable_verification: Enable state verification after actions
            max_retries: Maximum retry attempts for transient errors
        """
        self.agent = agent
        self.graph: Optional[StateGraph] = None
        self.cancel_event = cancel_event or threading.Event()
        self.enable_recovery = enable_recovery
        self.enable_verification = enable_verification
        self.retry_manager = RetryManager(max_retries=max_retries)
        
        # Track consecutive failures for loop prevention
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
        logger.info(
            f"Initialized EnhancedAgentEngine for agent: {agent.config.name} "
            f"(recovery={enable_recovery}, verification={enable_verification})"
        )
    
    def build_graph(self) -> StateGraph:
        """
        Build the execution graph with recovery and verification nodes.
        
        Returns:
            Configured StateGraph with error handling
        """
        workflow = StateGraph(AgentState)
        
        # Core ReAct nodes
        workflow.add_node("observe", self._observe_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("act", self._act_node)
        
        # Recovery and verification nodes
        if self.enable_recovery:
            workflow.add_node("recovery", self._recovery_node)
        
        if self.enable_verification:
            workflow.add_node("verify", self._verify_node)
        
        # Set entry point
        workflow.set_entry_point("observe")
        
        # Build edges based on configuration
        workflow.add_edge("observe", "reason")
        workflow.add_edge("reason", "act")
        
        # Act node routing: check for errors, then verify or continue
        if self.enable_verification:
            workflow.add_conditional_edges(
                "act",
                self._route_after_act,
                {
                    "verify": "verify",
                    "recovery": "recovery" if self.enable_recovery else "observe",
                    "end": END
                }
            )
            
            workflow.add_conditional_edges(
                "verify",
                self._route_after_verify,
                {
                    "continue": "observe",
                    "recovery": "recovery" if self.enable_recovery else "observe",
                    "end": END
                }
            )
        else:
            workflow.add_conditional_edges(
                "act",
                self._route_after_act_simple,
                {
                    "continue": "observe",
                    "recovery": "recovery" if self.enable_recovery else "observe",
                    "end": END
                }
            )
        
        # Recovery node routes back to observe (with context) or ends
        if self.enable_recovery:
            workflow.add_conditional_edges(
                "recovery",
                self._route_after_recovery,
                {
                    "retry": "observe",
                    "end": END
                }
            )
        
        self.graph = workflow.compile()
        logger.debug("Enhanced agent execution graph built with error handling")
        return self.graph
    
    def _observe_node(self, state: AgentState) -> AgentState:
        """Observation node with error handling."""
        try:
            observation = self.agent.observe(state)
            state['observations'].append(observation)
            
            # Reset consecutive failures on successful observation
            self.consecutive_failures = 0
            
            if self.agent.config.verbose:
                logger.debug(f"[Observe] {observation[:100]}...")
            
        except Exception as e:
            logger.error(f"Observation failed: {e}")
            state['error'] = f"Observation error: {str(e)}"
            state['metadata']['last_error_node'] = 'observe'
        
        return state
    
    def _reason_node(self, state: AgentState) -> AgentState:
        """Reasoning node with error handling."""
        try:
            observation = state['observations'][-1] if state['observations'] else ""
            reasoning = self.agent.reason(state, observation)
            state['reasoning'].append(reasoning)
            
            logger.info(f"[Reason]\n{reasoning}")
            
        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            state['error'] = f"Reasoning error: {str(e)}"
            state['metadata']['last_error_node'] = 'reason'
        
        return state
    
    def _act_node(self, state: AgentState) -> AgentState:
        """
        Action node with explicit ToolException handling.
        
        Implements the ToolException pattern from Section III.2:
        - Catches exceptions explicitly
        - Updates state with structured error message
        - Enables deterministic routing to recovery node
        """
        reasoning = state['reasoning'][-1] if state['reasoning'] else ""
        
        try:
            # Execute action with retry for transient errors
            action_result = self._execute_action_with_retry(state, reasoning)
            
            state['actions'].append(action_result)
            
            # Log action details
            action_name = action_result.get('action', 'unknown')
            success = action_result.get('success', False)
            
            logger.info(f"[Act] {action_name} | Success: {success}")
            
            # Track failures for loop prevention
            if not success:
                self.consecutive_failures += 1
                state['metadata']['consecutive_failures'] = self.consecutive_failures
            else:
                self.consecutive_failures = 0
                state['metadata']['consecutive_failures'] = 0
            
            # Update history
            state['history'].append({
                'step': state['current_step'],
                'observation': state['observations'][-1] if state['observations'] else "",
                'reasoning': reasoning,
                'action': action_result
            })
            
            # Increment step
            state['current_step'] += 1
            
        except (ToolException, ActionException) as e:
            # Explicit exception handling - route to recovery
            logger.warning(f"Tool/Action exception caught: {e}")
            
            self.consecutive_failures += 1
            state['metadata']['consecutive_failures'] = self.consecutive_failures
            state['metadata']['last_exception'] = {
                'type': e.__class__.__name__,
                'message': str(e),
                'retryable': getattr(e, 'retryable', True)
            }
            state['error'] = str(e)
            state['metadata']['last_error_node'] = 'act'
            
        except Exception as e:
            # Unexpected exception
            logger.exception(f"Unexpected error during action execution: {e}")
            
            self.consecutive_failures += 1
            state['metadata']['consecutive_failures'] = self.consecutive_failures
            state['error'] = f"Unexpected action error: {str(e)}"
            state['metadata']['last_error_node'] = 'act'
        
        return state
    
    def _execute_action_with_retry(
        self,
        state: AgentState,
        reasoning: str
    ) -> Dict[str, Any]:
        """
        Execute action with exponential backoff for transient errors.
        
        Args:
            state: Current agent state
            reasoning: Reasoning from previous step
            
        Returns:
            Action result dictionary
        """
        def action_fn():
            return self.agent.act(state, reasoning)
        
        try:
            return self.retry_manager.execute_with_retry(
                action_fn,
                exceptions=(ToolException, ActionException)
            )
        except Exception as e:
            # If retry exhausted, check if transient
            if is_transient_error(e):
                logger.warning(f"Transient error persisted after retries: {e}")
            raise
    
    def _verify_node(self, state: AgentState) -> AgentState:
        """
        State verification node after critical actions.
        
        Implements environment-based state verification from Section III.2:
        - Verifies expected state transitions occurred
        - Uses VLM to check actual state
        - Triggers recovery if verification fails
        """
        # Check if last action was critical (requires verification)
        if not state['actions']:
            return state
        
        last_action = state['actions'][-1]
        
        # Only verify if action succeeded initially
        if not last_action.get('success', False):
            return state
        
        try:
            # Perform verification based on action type
            verification_result = self._verify_action_result(state, last_action)
            
            state['metadata']['last_verification'] = verification_result
            
            if not verification_result.get('verified', False):
                logger.warning(
                    f"State verification failed: {verification_result.get('reason', 'Unknown')}"
                )
                state['error'] = f"Verification failed: {verification_result.get('reason')}"
                state['metadata']['last_error_node'] = 'verify'
            else:
                logger.debug("State verification passed")
                
        except Exception as e:
            logger.error(f"Verification error: {e}")
            state['error'] = f"Verification error: {str(e)}"
            state['metadata']['last_error_node'] = 'verify'
        
        return state
    
    def _verify_action_result(
        self,
        state: AgentState,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify action result using VLM or state checks.
        
        Args:
            state: Current agent state
            action: Action to verify
            
        Returns:
            Verification result dictionary
            
        Note:
            This is a basic implementation. For production use, extend with:
            - VLM-based visual verification (screenshot comparison)
            - Accessibility tree verification for GUI state
            - File system checks for file operations
            - API responses for network operations
        """
        action_type = action.get('action', 'unknown')
        
        # Basic verification based on action type
        # TODO: Implement VLM-based verification for GUI actions
        
        # For GUI actions, we can at least verify the action completed
        if action_type in ['click', 'type_text', 'press_key']:
            # In production, would use VLM to verify expected UI change
            # For now, rely on action success flag
            verified = action.get('success', False)
            method = 'action_success_flag'
        
        # For file operations, could verify file existence
        elif action_type == 'file_write':
            # Could add: check file exists and has expected content
            verified = action.get('success', False)
            method = 'action_success_flag'
        
        # For screen analysis, always assume valid
        elif action_type == 'analyze_screen':
            verified = action.get('success', False)
            method = 'analysis_success_flag'
        
        else:
            # Default: trust the action's success flag
            verified = action.get('success', False)
            method = 'basic_check'
        
        return {
            'verified': verified,
            'action_type': action_type,
            'method': method,
            'note': 'Basic verification - extend with VLM checks for production'
        }
    
    def _recovery_node(self, state: AgentState) -> AgentState:
        """
        Recovery node for handling failures.
        
        Implements recovery strategies:
        - Analyzes error type and context
        - Determines if retry is appropriate
        - Updates state for re-planning if needed
        """
        logger.info("[Recovery] Analyzing failure and determining recovery strategy")
        
        last_exception = state['metadata'].get('last_exception', {})
        error_node = state['metadata'].get('last_error_node', 'unknown')
        consecutive_failures = state['metadata'].get('consecutive_failures', 0)
        
        # Check if we've exceeded max consecutive failures
        if consecutive_failures >= self.max_consecutive_failures:
            logger.error(
                f"Max consecutive failures ({self.max_consecutive_failures}) reached, "
                "ending execution"
            )
            state['error'] = (
                f"Execution halted: {consecutive_failures} consecutive failures"
            )
            state['metadata']['recovery_decision'] = 'end'
            return state
        
        # Determine if error is retryable
        retryable = last_exception.get('retryable', False)
        
        if retryable and consecutive_failures < self.max_consecutive_failures:
            logger.info(f"Error is retryable, will retry (attempt {consecutive_failures + 1})")
            state['metadata']['recovery_decision'] = 'retry'
            
            # Add recovery context to observations
            recovery_context = (
                f"Recovery after failure in {error_node} node. "
                f"Previous error: {state.get('error', 'Unknown')}. "
                f"Attempting different approach."
            )
            state['observations'].append(recovery_context)
            
            # Clear error to allow retry
            state['error'] = None
        else:
            logger.warning("Error not retryable or max retries exceeded, ending execution")
            state['metadata']['recovery_decision'] = 'end'
        
        return state
    
    def _route_after_act(self, state: AgentState) -> str:
        """Route after act node (with verification enabled)."""
        if self.cancel_event.is_set():
            logger.warning("Stop requested by user")
            state['error'] = state.get('error') or "Stopped by user"
            return "end"
        
        # If error occurred, route to recovery
        if state.get('error'):
            return "recovery" if self.enable_recovery else "end"
        
        # Check if should continue
        if not self.agent.should_continue(state):
            return "end"
        
        # Verify state after action
        return "verify"
    
    def _route_after_act_simple(self, state: AgentState) -> str:
        """Route after act node (without verification)."""
        if self.cancel_event.is_set():
            logger.warning("Stop requested by user")
            state['error'] = state.get('error') or "Stopped by user"
            return "end"
        
        if state.get('error'):
            return "recovery" if self.enable_recovery else "end"
        
        if not self.agent.should_continue(state):
            return "end"
        
        return "continue"
    
    def _route_after_verify(self, state: AgentState) -> str:
        """Route after verify node."""
        if self.cancel_event.is_set():
            return "end"
        
        # If verification failed, route to recovery
        if state.get('error'):
            return "recovery" if self.enable_recovery else "end"
        
        # Check if should continue
        if not self.agent.should_continue(state):
            return "end"
        
        return "continue"
    
    def _route_after_recovery(self, state: AgentState) -> str:
        """Route after recovery node."""
        recovery_decision = state['metadata'].get('recovery_decision', 'end')
        
        if recovery_decision == 'retry':
            return "retry"
        
        return "end"
    
    def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        recursion_limit: int = 25
    ) -> AgentState:
        """
        Execute the agent using the enhanced graph.
        
        Args:
            task: Task description
            context: Optional context dictionary
            recursion_limit: Maximum number of graph iterations
            
        Returns:
            Final agent state
        """
        # Initialize state
        state = self.agent.initialize_state(task, context)
        
        # Reset failure tracking
        self.consecutive_failures = 0
        self.retry_manager.reset()
        
        # Build graph if not already built
        if not self.graph:
            self.build_graph()
        
        logger.info(f"Starting enhanced graph execution for task: {task}")
        logger.info(f"Recursion limit: {recursion_limit}")
        
        try:
            # Execute the graph
            final_state = self.graph.invoke(
                state,
                config={"recursion_limit": recursion_limit}
            )
            
            logger.info(
                f"Graph execution completed. Steps: {final_state['current_step']} "
                f"(limit: {recursion_limit})"
            )
            
            if final_state['current_step'] >= recursion_limit - 1:
                logger.warning(f"Recursion limit ({recursion_limit}) reached")
            
            return final_state
        
        except Exception as e:
            logger.exception(f"Error during graph execution: {e}")
            state['error'] = str(e)
            return state
