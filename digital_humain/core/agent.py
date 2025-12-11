"""Base agent implementation with multi-step reasoning capabilities."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum
from loguru import logger
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent role types."""
    COORDINATOR = "coordinator"
    EXECUTOR = "executor"
    ANALYZER = "analyzer"
    PLANNER = "planner"


class AgentState(TypedDict):
    """State container for agent execution."""
    task: str
    context: Dict[str, Any]
    history: List[Dict[str, Any]]
    current_step: int
    max_steps: int
    observations: List[str]
    reasoning: List[str]
    actions: List[Dict[str, Any]]
    result: Optional[Any]
    error: Optional[str]
    metadata: Dict[str, Any]


class AgentConfig(BaseModel):
    """Configuration for agent behavior."""
    name: str
    role: AgentRole
    model: str = "llama2"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_iterations: int = Field(default=10, ge=1, le=100)
    verbose: bool = True
    tools: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None


class BaseAgent(ABC):
    """
    Base agent class with multi-step reasoning capabilities.
    
    Implements the ReAct pattern (Reasoning + Acting):
    1. Observe current state
    2. Reason about next action
    3. Execute action
    4. Update state and repeat
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with configuration."""
        self.config = config
        self.state: Optional[AgentState] = None
        logger.info(f"Initialized agent: {config.name} ({config.role})")
    
    def initialize_state(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentState:
        """Initialize the agent state for a new task."""
        self.state = AgentState(
            task=task,
            context=context or {},
            history=[],
            current_step=0,
            max_steps=self.config.max_iterations,
            observations=[],
            reasoning=[],
            actions=[],
            result=None,
            error=None,
            metadata={"agent": self.config.name, "role": self.config.role.value}
        )
        logger.debug(f"State initialized for task: {task}")
        return self.state
    
    def observe(self, state: AgentState) -> str:
        """
        Observe the current state and environment.
        
        Args:
            state: Current agent state
            
        Returns:
            Observation string describing current situation
        """
        observation = f"Step {state['current_step']}/{state['max_steps']}\n"
        observation += f"Task: {state['task']}\n"
        
        if state['history']:
            observation += f"Previous actions: {len(state['history'])}\n"
            
        if state['observations']:
            observation += f"Latest observation: {state['observations'][-1]}\n"
            
        return observation
    
    @abstractmethod
    def reason(self, state: AgentState, observation: str) -> str:
        """
        Reason about what action to take next.
        
        Args:
            state: Current agent state
            observation: Current observation
            
        Returns:
            Reasoning explanation
        """
        pass
    
    @abstractmethod
    def act(self, state: AgentState, reasoning: str) -> Dict[str, Any]:
        """
        Execute an action based on reasoning.
        
        Args:
            state: Current agent state
            reasoning: Reasoning from previous step
            
        Returns:
            Action result dictionary
        """
        pass
    
    def should_continue(self, state: AgentState) -> bool:
        """
        Determine if the agent should continue execution.
        
        Args:
            state: Current agent state
            
        Returns:
            True if should continue, False otherwise
        """
        if state['error']:
            logger.error(f"Stopping due to error: {state['error']}")
            return False
            
        if state['result'] is not None:
            logger.info("Task completed successfully")
            return False
            
        if state['current_step'] >= state['max_steps']:
            logger.warning(f"Max steps ({state['max_steps']}) reached")
            return False
            
        return True
    
    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentState:
        """
        Execute the agent's main loop.
        
        Args:
            task: Task description
            context: Optional context dictionary
            
        Returns:
            Final agent state
        """
        state = self.initialize_state(task, context)
        
        logger.info(f"Starting agent execution for task: {task}")
        
        try:
            while self.should_continue(state):
                # Observe
                observation = self.observe(state)
                state['observations'].append(observation)
                
                if self.config.verbose:
                    logger.debug(f"Observation: {observation[:200]}...")
                
                # Reason
                reasoning = self.reason(state, observation)
                state['reasoning'].append(reasoning)
                
                if self.config.verbose:
                    logger.info(f"Reasoning: {reasoning[:200]}...")
                
                # Act
                action_result = self.act(state, reasoning)
                state['actions'].append(action_result)
                
                if self.config.verbose:
                    logger.info(f"Action: {action_result.get('action', 'unknown')}")
                
                # Update history
                state['history'].append({
                    'step': state['current_step'],
                    'observation': observation,
                    'reasoning': reasoning,
                    'action': action_result
                })
                
                # Increment step
                state['current_step'] += 1
                
        except Exception as e:
            logger.exception(f"Error during agent execution: {e}")
            state['error'] = str(e)
        
        logger.info(f"Agent execution completed. Steps: {state['current_step']}")
        return state
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        if self.config.system_prompt:
            return self.config.system_prompt
        
        return f"""You are a {self.config.role.value} agent specialized in desktop automation.
Your role is to help with enterprise tasks including HBYS, Accounting, and Quality processes.

You can:
1. Analyze screenshots and understand GUI elements
2. Plan multi-step actions to complete tasks
3. Execute desktop automation commands
4. Handle unstructured data and adapt to different scenarios

Always think step-by-step and explain your reasoning before taking action.
"""
