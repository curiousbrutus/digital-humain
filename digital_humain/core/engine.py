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
        
        if self.agent.config.verbose:
            logger.info(f"[Reason] {reasoning[:100]}...")
        
        return state
    
    def _act_node(self, state: AgentState) -> AgentState:
        """Action node in the graph."""
        reasoning = state['reasoning'][-1] if state['reasoning'] else ""
        
        try:
            action_result = self.agent.act(state, reasoning)
            state['actions'].append(action_result)
            
            if self.agent.config.verbose:
                logger.info(f"[Act] {action_result.get('action', 'unknown')}")
            
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
    
    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentState:
        """
        Execute the agent using the graph.
        
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
        
        logger.info(f"Starting graph execution for task: {task}")
        
        try:
            # Execute the graph
            final_state = self.graph.invoke(state)
            logger.info(f"Graph execution completed. Steps: {final_state['current_step']}")
            return final_state
        
        except Exception as e:
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
