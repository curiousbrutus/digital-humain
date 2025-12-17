"""Orchestration Engine (OE) - Central control plane for task decomposition and tool routing."""

from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field
from loguru import logger

from digital_humain.core.agent import AgentRole, AgentState
from digital_humain.tools.base import ToolRegistry
from digital_humain.memory.hierarchical_memory import HierarchicalMemoryManager
from digital_humain.core.audit_recovery import AuditRecoveryEngine


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class SubTask(BaseModel):
    """A decomposed sub-task."""
    
    id: str
    description: str
    role: AgentRole
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)
    tools_required: List[str] = Field(default_factory=list)
    estimated_steps: int = 5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskDecomposition(BaseModel):
    """Result of task decomposition."""
    
    original_task: str
    subtasks: List[SubTask]
    execution_order: List[str]  # IDs in execution order
    total_estimated_steps: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrchestrationEngine:
    """
    Orchestration Engine for centralized task management.
    
    Features:
    - Task decomposition into subtasks
    - Tool routing based on task requirements
    - Execution planning with dependency resolution
    - Integration with HMM for context management
    - Integration with ARE for audit logging
    """
    
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        memory_manager: Optional[HierarchicalMemoryManager] = None,
        audit_engine: Optional[AuditRecoveryEngine] = None
    ):
        """
        Initialize the Orchestration Engine.
        
        Args:
            tool_registry: Tool registry for tool routing
            memory_manager: Hierarchical memory manager
            audit_engine: Audit & recovery engine
        """
        self.tool_registry = tool_registry or ToolRegistry()
        self.memory_manager = memory_manager or HierarchicalMemoryManager()
        self.audit_engine = audit_engine or AuditRecoveryEngine()
        
        self.subtask_counter = 0
        
        logger.info("OrchestrationEngine initialized")
    
    def decompose_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskDecomposition:
        """
        Decompose a high-level task into subtasks.
        
        Args:
            task: Task description
            context: Optional context for decomposition
            
        Returns:
            TaskDecomposition result
        """
        logger.info(f"Decomposing task: {task}")
        
        subtasks = []
        task_lower = task.lower()
        
        # Rule-based decomposition (in production, this would use an LLM)
        
        # 1. Browser automation tasks
        if any(keyword in task_lower for keyword in ["browser", "web", "website", "navigate", "url"]):
            subtasks.append(self._create_subtask(
                description=f"Open browser and navigate to target",
                role=AgentRole.EXECUTOR,
                priority=TaskPriority.HIGH,
                tools_required=["browser_navigate", "browser_wait"]
            ))
            
            if any(keyword in task_lower for keyword in ["fill", "form", "input", "type"]):
                subtasks.append(self._create_subtask(
                    description=f"Fill out form fields",
                    role=AgentRole.EXECUTOR,
                    priority=TaskPriority.MEDIUM,
                    tools_required=["browser_fill", "browser_click"],
                    dependencies=[subtasks[-1].id] if subtasks else []
                ))
            
            if any(keyword in task_lower for keyword in ["submit", "click", "button"]):
                subtasks.append(self._create_subtask(
                    description=f"Submit form or click button",
                    role=AgentRole.EXECUTOR,
                    priority=TaskPriority.MEDIUM,
                    tools_required=["browser_click"],
                    dependencies=[subtasks[-1].id] if subtasks else []
                ))
        
        # 2. File system tasks
        if any(keyword in task_lower for keyword in ["file", "read", "write", "save", "open document"]):
            subtasks.append(self._create_subtask(
                description=f"Perform file system operations",
                role=AgentRole.EXECUTOR,
                priority=TaskPriority.MEDIUM,
                tools_required=["file_read", "file_write", "file_list"]
            ))
        
        # 3. Desktop application tasks
        if any(keyword in task_lower for keyword in ["open", "launch", "application", "app"]):
            subtasks.append(self._create_subtask(
                description=f"Launch desktop application",
                role=AgentRole.EXECUTOR,
                priority=TaskPriority.HIGH,
                tools_required=["system_launch_app"]
            ))
        
        # 4. Analysis tasks
        if any(keyword in task_lower for keyword in ["analyze", "analyze screen", "identify", "detect"]):
            subtasks.append(self._create_subtask(
                description=f"Analyze screen or data",
                role=AgentRole.ANALYZER,
                priority=TaskPriority.HIGH,
                tools_required=["screen_capture", "vlm_analyze"]
            ))
        
        # 5. Planning tasks
        if any(keyword in task_lower for keyword in ["plan", "strategy", "organize", "schedule"]):
            subtasks.append(self._create_subtask(
                description=f"Create execution plan",
                role=AgentRole.PLANNER,
                priority=TaskPriority.CRITICAL,
                tools_required=[]
            ))
        
        # 6. Data entry tasks
        if any(keyword in task_lower for keyword in ["type", "enter", "input", "write"]):
            subtasks.append(self._create_subtask(
                description=f"Enter data or text",
                role=AgentRole.EXECUTOR,
                priority=TaskPriority.MEDIUM,
                tools_required=["gui_type", "gui_click"]
            ))
        
        # If no specific subtasks identified, create a general one
        if not subtasks:
            subtasks.append(self._create_subtask(
                description=task,
                role=AgentRole.EXECUTOR,
                priority=TaskPriority.MEDIUM,
                tools_required=[]
            ))
        
        # Resolve execution order based on dependencies
        execution_order = self._resolve_execution_order(subtasks)
        
        # Calculate total estimated steps
        total_steps = sum(st.estimated_steps for st in subtasks)
        
        decomposition = TaskDecomposition(
            original_task=task,
            subtasks=subtasks,
            execution_order=execution_order,
            total_estimated_steps=total_steps
        )
        
        logger.info(f"Task decomposed into {len(subtasks)} subtasks (estimated {total_steps} steps)")
        
        return decomposition
    
    def route_tools(self, subtask: SubTask) -> List[str]:
        """
        Route tools for a subtask based on requirements.
        
        Args:
            subtask: SubTask to route tools for
            
        Returns:
            List of available tool names
        """
        required_tools = subtask.tools_required
        available_tools = []
        
        for tool_name in required_tools:
            # Check if tool exists in registry
            tool = self.tool_registry.get(tool_name)
            if tool:
                available_tools.append(tool_name)
            else:
                logger.warning(f"Required tool '{tool_name}' not found in registry")
        
        # If no specific tools required, provide all available tools
        if not required_tools:
            available_tools = self.tool_registry.list_tools()
        
        logger.debug(f"Routed {len(available_tools)} tools for subtask {subtask.id}")
        return available_tools
    
    def create_execution_plan(
        self,
        decomposition: TaskDecomposition
    ) -> List[Dict[str, Any]]:
        """
        Create a detailed execution plan from decomposition.
        
        Args:
            decomposition: TaskDecomposition result
            
        Returns:
            List of execution steps with context
        """
        execution_plan = []
        
        for subtask_id in decomposition.execution_order:
            # Find the subtask
            subtask = next((st for st in decomposition.subtasks if st.id == subtask_id), None)
            
            if not subtask:
                logger.error(f"Subtask {subtask_id} not found in decomposition")
                continue
            
            # Route tools
            available_tools = self.route_tools(subtask)
            
            # Create execution step
            step = {
                "subtask_id": subtask.id,
                "description": subtask.description,
                "role": subtask.role.value,
                "priority": subtask.priority.value,
                "available_tools": available_tools,
                "estimated_steps": subtask.estimated_steps,
                "dependencies_met": True  # In practice, check actual dependencies
            }
            
            execution_plan.append(step)
        
        logger.info(f"Created execution plan with {len(execution_plan)} steps")
        return execution_plan
    
    def update_subtask_status(
        self,
        subtask_id: str,
        status: TaskStatus,
        result: Optional[Any] = None
    ) -> None:
        """
        Update the status of a subtask.
        
        Args:
            subtask_id: ID of the subtask
            status: New status
            result: Optional result data
        """
        # Store in memory manager
        self.memory_manager.add_to_context(
            key=f"subtask_status_{subtask_id}",
            content={
                "subtask_id": subtask_id,
                "status": status.value,
                "result": result
            },
            priority=7
        )
        
        logger.info(f"Subtask {subtask_id} status updated to {status.value}")
    
    def get_context_for_subtask(
        self,
        subtask: SubTask,
        decomposition: TaskDecomposition
    ) -> Dict[str, Any]:
        """
        Get relevant context for executing a subtask.
        
        Args:
            subtask: SubTask to execute
            decomposition: Full task decomposition
            
        Returns:
            Context dictionary
        """
        # Get main context summary
        main_context = self.memory_manager.get_main_context_summary()
        
        # Get results from dependencies
        dependency_results = {}
        for dep_id in subtask.dependencies:
            result = self.memory_manager.get_from_context(f"subtask_status_{dep_id}")
            if result:
                dependency_results[dep_id] = result
        
        # Search AKB for relevant past experiences
        relevant_pages = self.memory_manager.search_and_page_in(
            query=subtask.description,
            min_priority=5,
            limit=3
        )
        
        context = {
            "original_task": decomposition.original_task,
            "subtask": subtask.model_dump(),
            "main_context": main_context,
            "dependency_results": dependency_results,
            "relevant_past_experiences": len(relevant_pages),
            "available_tools": self.route_tools(subtask)
        }
        
        return context
    
    def _create_subtask(
        self,
        description: str,
        role: AgentRole,
        priority: TaskPriority,
        tools_required: List[str],
        dependencies: Optional[List[str]] = None,
        estimated_steps: int = 5
    ) -> SubTask:
        """Create a subtask with auto-generated ID."""
        self.subtask_counter += 1
        subtask_id = f"subtask_{self.subtask_counter:03d}"
        
        return SubTask(
            id=subtask_id,
            description=description,
            role=role,
            priority=priority,
            tools_required=tools_required,
            dependencies=dependencies or [],
            estimated_steps=estimated_steps
        )
    
    def _resolve_execution_order(self, subtasks: List[SubTask]) -> List[str]:
        """
        Resolve execution order based on dependencies.
        
        Uses topological sort to handle dependencies.
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            List of subtask IDs in execution order
        """
        # Build dependency graph
        graph = {st.id: st.dependencies for st in subtasks}
        in_degree = {st.id: 0 for st in subtasks}
        
        # Calculate in-degrees (count how many dependencies each task has)
        for st_id, deps in graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[st_id] += 1
        
        # Topological sort using Kahn's algorithm
        queue = [st_id for st_id, degree in in_degree.items() if degree == 0]
        order = []
        
        while queue:
            # Sort by priority for deterministic ordering
            queue.sort(key=lambda x: next((st.priority.value for st in subtasks if st.id == x), ""))
            
            current = queue.pop(0)
            order.append(current)
            
            # Update in-degrees
            for st_id, deps in graph.items():
                if current in deps:
                    in_degree[st_id] -= 1
                    if in_degree[st_id] == 0 and st_id not in order:
                        queue.append(st_id)
        
        # Check for cycles
        if len(order) != len(subtasks):
            logger.warning("Circular dependencies detected, using fallback ordering")
            order = [st.id for st in subtasks]
        
        return order
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the orchestration engine."""
        memory_stats = self.memory_manager.get_stats()
        audit_stats = self.audit_engine.get_stats()
        
        return {
            "tool_registry": {
                "total_tools": len(self.tool_registry.list_tools())
            },
            "memory_manager": memory_stats,
            "audit_engine": audit_stats,
            "subtasks_created": self.subtask_counter
        }
