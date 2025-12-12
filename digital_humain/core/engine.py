"""Agent execution engine with LangGraph integration."""

from typing import Any, Dict, List, Optional, Callable
from langgraph.graph import StateGraph, END
from loguru import logger

from digital_humain.core.agent import AgentState, BaseAgent


class AgentEngine:
    """
    Agent execution engine using LangGraph for state management.
    
    Provides graph-based orchestration for complex agent workflows.
    """
    
    def __init__(self, agent: BaseAgent):
        """
        Initialize the engine with an agent.
        
        Args:
            agent: Agent instance to execute
        """
        self.agent = agent
        self.graph: Optional[StateGraph] = None
        logger.info(f"Initialized AgentEngine for agent: {agent.config.name}")
    
    def build_graph(self) -> StateGraph:
        """
        Build the execution graph for the agent.
        
        Returns:
            Configured StateGraph
        """
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("observe", self._observe_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("act", self._act_node)
        
        # Set entry point
        workflow.set_entry_point("observe")
        
        # Add edges
        workflow.add_edge("observe", "reason")
        workflow.add_edge("reason", "act")
        
        # Add conditional edge from act
        workflow.add_conditional_edges(
            "act",
            self._should_continue,
            {
                "continue": "observe",
                "end": END
            }
        )
        
        self.graph = workflow.compile()
        logger.debug("Agent execution graph built")
        return self.graph
    
    def _observe_node(self, state: AgentState) -> AgentState:
        """Observation node in the graph."""
        observation = self.agent.observe(state)
        state['observations'].append(observation)
        
        if self.agent.config.verbose:
            logger.debug(f"[Observe] {observation[:100]}...")
        
        return state
    
    def _reason_node(self, state: AgentState) -> AgentState:
        """Reasoning node in the graph."""
        observation = state['observations'][-1] if state['observations'] else ""
        reasoning = self.agent.reason(state, observation)
        state['reasoning'].append(reasoning)

        # Always show the full reasoning so operators can follow the chain of thought
        logger.info(f"[Reason]\n{reasoning}")

        return state
    
    def _act_node(self, state: AgentState) -> AgentState:
        """Action node in the graph."""
        reasoning = state['reasoning'][-1] if state['reasoning'] else ""
        
        try:
            action_result = self.agent.act(state, reasoning)
            state['actions'].append(action_result)
            
            # Log action result with key details
            action_name = action_result.get('action', 'unknown')
            success = action_result.get('success', False)
            
            # Build compact param summary
            params_summary = []
            if 'text' in action_result:
                text = action_result['text']
                params_summary.append(f"text='{text[:30]}...'")
            if 'key' in action_result:
                params_summary.append(f"key={action_result['key']}")
            if 'app_name' in action_result:
                params_summary.append(f"app={action_result['app_name']}")
            if 'position' in action_result and action_result['position']:
                params_summary.append(f"pos={action_result['position']}")
            
            params_str = ", ".join(params_summary) if params_summary else ""
            logger.info(f"[Act] {action_name} | Success: {success} | {params_str}")
            
            # Update history
            state['history'].append({
                'step': state['current_step'],
                'observation': state['observations'][-1] if state['observations'] else "",
                'reasoning': reasoning,
                'action': action_result
            })
            
            # Increment step
            state['current_step'] += 1
            
        except Exception as e:
            logger.exception(f"Error during action execution: {e}")
            state['error'] = str(e)
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if execution should continue."""
        if self.agent.should_continue(state):
            return "continue"
        return "end"
    
    def run(self, task: str, context: Optional[Dict[str, Any]] = None, recursion_limit: int = 25) -> AgentState:
        """
        Execute the agent using the graph.
        
        Args:
            task: Task description
            context: Optional context dictionary
            recursion_limit: Maximum number of graph iterations
            
        Returns:
            Final agent state
        """
        # Initialize state
        state = self.agent.initialize_state(task, context)
        
        # Build graph if not already built
        if not self.graph:
            self.build_graph()
        
        logger.info(f"Starting graph execution for task: {task}")
        logger.info(f"Recursion limit set to: {recursion_limit}")
        
        try:
            # Execute the graph
            final_state = self.graph.invoke(state, config={"recursion_limit": recursion_limit})
            logger.info(f"Graph execution completed. Steps taken: {final_state['current_step']} (limit: {recursion_limit})")
            
            # Warn if limit was reached
            if final_state['current_step'] >= recursion_limit - 1:
                logger.warning(f"Recursion limit ({recursion_limit}) reached. Task may be incomplete.")
            
            return final_state
        
        except Exception as e:
            error_msg = str(e)
            if "recursion limit" in error_msg.lower():
                logger.error(f"Recursion limit ({recursion_limit}) exceeded during graph execution. Consider increasing limit in GUI.")
            else:
                logger.exception(f"Error during graph execution: {e}")
            state['error'] = str(e)
            return state
    
    async def run_async(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Execute the agent asynchronously using the graph.
        
        Args:
            task: Task description
            context: Optional context dictionary
            
        Returns:
            Final agent state
        """
        # Initialize state
        state = self.agent.initialize_state(task, context)
        
        # Build graph if not already built
        if not self.graph:
            self.build_graph()
        
        logger.info(f"Starting async graph execution for task: {task}")
        
        try:
            # Execute the graph asynchronously
            final_state = await self.graph.ainvoke(state)
            logger.info(f"Async graph execution completed. Steps: {final_state['current_step']}")
            return final_state
        
        except Exception as e:
            logger.exception(f"Error during async graph execution: {e}")
            state['error'] = str(e)
            return state
