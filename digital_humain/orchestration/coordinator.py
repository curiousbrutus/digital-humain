"""Multi-agent coordinator for task orchestration."""

from typing import Any, Dict, List, Optional
from loguru import logger

from digital_humain.core.agent import BaseAgent, AgentRole, AgentState
from digital_humain.orchestration.registry import AgentRegistry
from digital_humain.orchestration.memory import SharedMemory


class AgentCoordinator:
    """
    Coordinates multiple agents for complex task execution.
    
    Implements Letta-like multi-agent orchestration with:
    - Task decomposition
    - Agent selection and delegation
    - Result aggregation
    - Shared context management
    """
    
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        memory: Optional[SharedMemory] = None
    ):
        """
        Initialize the coordinator.
        
        Args:
            registry: Agent registry (creates new if not provided)
            memory: Shared memory (creates new if not provided)
        """
        self.registry = registry or AgentRegistry()
        self.memory = memory or SharedMemory()
        self.execution_history: List[Dict[str, Any]] = []
        logger.info("Initialized AgentCoordinator")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the coordinator.
        
        Args:
            agent: Agent to register
        """
        self.registry.register(agent)
    
    def decompose_task(self, task: str) -> List[Dict[str, Any]]:
        """
        Decompose a complex task into subtasks.
        
        Args:
            task: Task description
            
        Returns:
            List of subtask dictionaries
        """
        # Simple decomposition - in practice would use LLM
        # For now, we'll use a rule-based approach
        
        subtasks = []
        
        # Check for common patterns
        if "analyze" in task.lower():
            subtasks.append({
                "description": f"Analyze: {task}",
                "role": AgentRole.ANALYZER,
                "priority": 1
            })
        
        if any(word in task.lower() for word in ["plan", "schedule", "organize"]):
            subtasks.append({
                "description": f"Plan: {task}",
                "role": AgentRole.PLANNER,
                "priority": 1
            })
        
        if any(word in task.lower() for word in ["execute", "run", "perform", "do"]):
            subtasks.append({
                "description": f"Execute: {task}",
                "role": AgentRole.EXECUTOR,
                "priority": 2
            })
        
        # If no specific subtasks, create a general one
        if not subtasks:
            subtasks.append({
                "description": task,
                "role": AgentRole.COORDINATOR,
                "priority": 1
            })
        
        logger.info(f"Decomposed task into {len(subtasks)} subtasks")
        return subtasks
    
    def select_agent(self, subtask: Dict[str, Any]) -> Optional[BaseAgent]:
        """
        Select the best agent for a subtask.
        
        Args:
            subtask: Subtask dictionary
            
        Returns:
            Selected agent or None
        """
        required_role = subtask.get("role", AgentRole.COORDINATOR)
        
        # Get agents with matching role
        candidates = self.registry.get_by_role(required_role)
        
        if not candidates:
            # Fall back to any available agent
            all_agents = [
                self.registry.get(name)
                for name in self.registry.list_agents()
            ]
            candidates = [a for a in all_agents if a is not None]
        
        if not candidates:
            logger.warning(f"No suitable agent found for role: {required_role}")
            return None
        
        # Select first available agent (could be more sophisticated)
        selected = candidates[0]
        logger.info(f"Selected agent: {selected.config.name} for subtask")
        return selected
    
    def delegate_task(
        self,
        agent: BaseAgent,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Delegate a task to a specific agent.
        
        Args:
            agent: Agent to execute task
            task: Task description
            context: Optional context
            
        Returns:
            Agent execution state
        """
        logger.info(f"Delegating to agent: {agent.config.name}")
        
        # Merge shared memory into context
        full_context = context or {}
        full_context["shared_memory"] = self.memory.get_all()
        
        # Execute task
        result = agent.run(task, full_context)
        
        # Update shared memory with results
        if result.get("result"):
            self.memory.set(
                f"result_{agent.config.name}",
                result["result"],
                agent.config.name
            )
        
        # Record execution
        self.execution_history.append({
            "agent": agent.config.name,
            "task": task,
            "steps": result["current_step"],
            "success": result.get("error") is None,
            "result": result.get("result")
        })
        
        return result
    
    def execute_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using multiple agents.
        
        Args:
            task: Task description
            context: Optional context
            
        Returns:
            Execution results
        """
        logger.info(f"Coordinating task: {task}")
        
        # Store task in memory
        self.memory.set("current_task", task, "coordinator")
        
        # Decompose task
        subtasks = self.decompose_task(task)
        
        # Execute subtasks
        results = []
        for subtask in subtasks:
            # Select agent
            agent = self.select_agent(subtask)
            
            if not agent:
                logger.error(f"No agent available for subtask: {subtask['description']}")
                results.append({
                    "subtask": subtask,
                    "success": False,
                    "error": "No agent available"
                })
                continue
            
            # Delegate and execute
            result = self.delegate_task(agent, subtask["description"], context)
            
            results.append({
                "subtask": subtask,
                "agent": agent.config.name,
                "success": result.get("error") is None,
                "result": result.get("result"),
                "steps": result["current_step"]
            })
        
        # Aggregate results
        overall_success = all(r.get("success", False) for r in results)
        
        final_result = {
            "task": task,
            "success": overall_success,
            "subtasks": len(subtasks),
            "results": results,
            "total_steps": sum(r.get("steps", 0) for r in results)
        }
        
        # Store in memory
        self.memory.set("final_result", final_result, "coordinator")
        
        logger.info(
            f"Task completed: {overall_success} "
            f"({len(subtasks)} subtasks, {final_result['total_steps']} steps)"
        )
        
        return final_result
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get execution history.
        
        Returns:
            List of execution records
        """
        return self.execution_history.copy()
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self.execution_history.clear()
        logger.info("Execution history cleared")
