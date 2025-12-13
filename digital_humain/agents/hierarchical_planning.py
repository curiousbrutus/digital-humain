"""Hierarchical Planning architecture for long-horizon desktop automation.

Implements the two-tier agent system from Section III.1:
- High-level Planner Agent: Breaks down tasks into milestones
- Lower-level Worker Agent: Executes localized ReAct loops per milestone

This architecture provides:
- Long-horizon task decomposition into measurable subgoals
- Balanced local adaptation with global guidance
- Clear failure nodes and milestone-based re-planning
- Prevention of local failures from becoming global abandonment
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from loguru import logger
from pydantic import BaseModel, Field

from digital_humain.core.agent import BaseAgent, AgentConfig, AgentState, AgentRole
from digital_humain.core.llm import LLMProvider
from digital_humain.core.exceptions import PlanningException


class MilestoneStatus(str, Enum):
    """Status of a milestone in the plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Milestone(BaseModel):
    """Represents a high-level milestone/subgoal."""
    id: str
    description: str
    status: MilestoneStatus = MilestoneStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)
    success_criteria: Optional[str] = None
    max_attempts: int = 3
    attempts: int = 0
    error_message: Optional[str] = None
    
    def can_start(self, completed_milestones: List[str]) -> bool:
        """Check if milestone can start based on dependencies."""
        return all(dep in completed_milestones for dep in self.dependencies)
    
    def mark_in_progress(self) -> None:
        """Mark milestone as in progress."""
        self.status = MilestoneStatus.IN_PROGRESS
        self.attempts += 1
    
    def mark_completed(self) -> None:
        """Mark milestone as completed."""
        self.status = MilestoneStatus.COMPLETED
    
    def mark_failed(self, error: str) -> None:
        """Mark milestone as failed."""
        self.status = MilestoneStatus.FAILED
        self.error_message = error
    
    def can_retry(self) -> bool:
        """Check if milestone can be retried."""
        return self.attempts < self.max_attempts


class TaskPlan(BaseModel):
    """Represents a hierarchical task plan."""
    task: str
    milestones: List[Milestone] = Field(default_factory=list)
    current_milestone_id: Optional[str] = None
    completed_milestone_ids: List[str] = Field(default_factory=list)
    
    def get_current_milestone(self) -> Optional[Milestone]:
        """Get the current milestone."""
        if not self.current_milestone_id:
            return None
        
        for milestone in self.milestones:
            if milestone.id == self.current_milestone_id:
                return milestone
        return None
    
    def get_next_milestone(self) -> Optional[Milestone]:
        """Get the next milestone to execute."""
        for milestone in self.milestones:
            if milestone.status == MilestoneStatus.PENDING:
                if milestone.can_start(self.completed_milestone_ids):
                    return milestone
        return None
    
    def mark_milestone_completed(self, milestone_id: str) -> None:
        """Mark a milestone as completed."""
        for milestone in self.milestones:
            if milestone.id == milestone_id:
                milestone.mark_completed()
                self.completed_milestone_ids.append(milestone_id)
                break
    
    def is_complete(self) -> bool:
        """Check if all milestones are completed."""
        return len(self.completed_milestone_ids) == len(self.milestones)
    
    def has_failed_milestones(self) -> bool:
        """Check if any milestones have failed."""
        return any(m.status == MilestoneStatus.FAILED for m in self.milestones)


class PlannerAgent(BaseAgent):
    """
    High-level Planner Agent (LLM-A).
    
    Responsibilities:
    - Breaks down complex tasks into measurable milestones
    - Provides clear overall direction
    - Performs global re-planning on Worker failures
    - Maintains sight of final objective
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm_provider: LLMProvider
    ):
        """
        Initialize the planner agent.
        
        Args:
            config: Agent configuration
            llm_provider: LLM provider for planning
        """
        super().__init__(config)
        self.llm = llm_provider
        logger.info(f"Initialized PlannerAgent: {config.name}")
    
    def create_plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """
        Create a hierarchical plan for the task.
        
        Args:
            task: High-level task description
            context: Optional context information
            
        Returns:
            TaskPlan with milestones
        """
        logger.info(f"Creating plan for task: {task}")
        
        # Build planning prompt
        planning_prompt = f"""Task: {task}

Break down this task into 3-5 measurable, high-level milestones or subgoals.
Each milestone should:
1. Be specific and measurable
2. Have clear success criteria
3. Build logically on previous milestones
4. Contribute to the final objective

Context: {context if context else 'None provided'}

Provide milestones in this format:
MILESTONE 1: [Description]
SUCCESS: [How to verify completion]

MILESTONE 2: [Description]
SUCCESS: [How to verify completion]

...

Milestones:"""
        
        try:
            response = self.llm.generate_sync(
                prompt=planning_prompt,
                system_prompt=self._get_planner_system_prompt(),
                temperature=0.3,  # Lower temperature for more structured planning
                max_tokens=1000
            )
            
            # Parse response into milestones
            milestones = self._parse_milestones(response, task)
            
            plan = TaskPlan(task=task, milestones=milestones)
            
            logger.info(f"Created plan with {len(milestones)} milestones")
            for i, milestone in enumerate(milestones):
                logger.debug(f"  Milestone {i+1}: {milestone.description}")
            
            return plan
        
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            raise PlanningException(phase="decomposition", message=str(e))
    
    def replan_on_failure(
        self,
        plan: TaskPlan,
        failed_milestone: Milestone,
        error_context: str
    ) -> TaskPlan:
        """
        Perform global re-planning after Worker failure.
        
        Args:
            plan: Current task plan
            failed_milestone: Milestone that failed
            error_context: Error details from Worker
            
        Returns:
            Updated TaskPlan
        """
        logger.info(
            f"Re-planning after failure on milestone: {failed_milestone.description}"
        )
        
        # Build re-planning prompt with failure context
        replan_prompt = f"""Original Task: {plan.task}

Failed Milestone: {failed_milestone.description}
Error Context: {error_context}

Completed Milestones:
{self._format_completed_milestones(plan)}

Remaining Milestones:
{self._format_remaining_milestones(plan)}

The current milestone failed after {failed_milestone.attempts} attempts.
Analyze the failure and either:
1. Suggest a modified approach for the failed milestone
2. Break down the failed milestone into smaller sub-milestones
3. Identify if a previous milestone needs to be revisited

Provide updated milestones starting from the current position:"""
        
        try:
            response = self.llm.generate_sync(
                prompt=replan_prompt,
                system_prompt=self._get_planner_system_prompt(),
                temperature=0.5,  # Slightly higher for creative problem-solving
                max_tokens=1000
            )
            
            # Parse new milestones
            new_milestones = self._parse_milestones(response, plan.task)
            
            # Update plan by replacing remaining milestones
            updated_plan = self._merge_plan_updates(plan, new_milestones)
            
            logger.info(f"Re-planned with {len(updated_plan.milestones)} total milestones")
            
            return updated_plan
        
        except Exception as e:
            logger.error(f"Re-planning failed: {e}")
            raise PlanningException(phase="replan", message=str(e))
    
    def _parse_milestones(self, response: str, task: str) -> List[Milestone]:
        """Parse LLM response into Milestone objects."""
        milestones = []
        lines = response.strip().split('\n')
        
        current_milestone = None
        milestone_counter = 0
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('MILESTONE'):
                # Save previous milestone
                if current_milestone:
                    milestones.append(current_milestone)
                
                # Extract description
                parts = line.split(':', 1)
                if len(parts) > 1:
                    description = parts[1].strip()
                else:
                    description = line
                
                milestone_counter += 1
                current_milestone = Milestone(
                    id=f"milestone_{milestone_counter}",
                    description=description
                )
            
            elif line.startswith('SUCCESS:') and current_milestone:
                # Extract success criteria
                parts = line.split(':', 1)
                if len(parts) > 1:
                    current_milestone.success_criteria = parts[1].strip()
        
        # Save last milestone
        if current_milestone:
            milestones.append(current_milestone)
        
        # Fallback if parsing failed
        if not milestones:
            logger.warning("Failed to parse milestones, creating default plan")
            milestones = [
                Milestone(
                    id="milestone_1",
                    description=f"Analyze requirements for: {task}",
                    success_criteria="Requirements clearly identified"
                ),
                Milestone(
                    id="milestone_2",
                    description=f"Execute main steps for: {task}",
                    success_criteria="Primary actions completed"
                ),
                Milestone(
                    id="milestone_3",
                    description=f"Verify completion of: {task}",
                    success_criteria="Task objectives met"
                )
            ]
        
        return milestones
    
    def _format_completed_milestones(self, plan: TaskPlan) -> str:
        """Format completed milestones for prompt."""
        completed = [
            m for m in plan.milestones
            if m.id in plan.completed_milestone_ids
        ]
        
        if not completed:
            return "None"
        
        return "\n".join(
            f"- {m.description}" for m in completed
        )
    
    def _format_remaining_milestones(self, plan: TaskPlan) -> str:
        """Format remaining milestones for prompt."""
        remaining = [
            m for m in plan.milestones
            if m.id not in plan.completed_milestone_ids
        ]
        
        if not remaining:
            return "None"
        
        return "\n".join(
            f"- {m.description} (Status: {m.status.value})" for m in remaining
        )
    
    def _merge_plan_updates(self, old_plan: TaskPlan, new_milestones: List[Milestone]) -> TaskPlan:
        """Merge new milestones into existing plan."""
        # Keep completed milestones, replace pending/failed ones
        updated_milestones = [
            m for m in old_plan.milestones
            if m.id in old_plan.completed_milestone_ids
        ]
        
        # Add new milestones
        updated_milestones.extend(new_milestones)
        
        return TaskPlan(
            task=old_plan.task,
            milestones=updated_milestones,
            completed_milestone_ids=old_plan.completed_milestone_ids
        )
    
    def _get_planner_system_prompt(self) -> str:
        """Get system prompt for planner agent."""
        return """You are a strategic planning agent for desktop automation tasks.

Your role is to:
1. Break down complex tasks into clear, measurable milestones
2. Maintain sight of the overall objective
3. Re-plan intelligently when execution fails
4. Provide global guidance to worker agents

Key principles:
- Each milestone should have clear success criteria
- Milestones should build logically on each other
- Plans should be adaptive but goal-oriented
- Consider potential failure points and alternatives

Always think strategically about the task structure and dependencies."""
    
    def reason(self, state: AgentState, observation: str) -> str:
        """Planner reasoning (not used in hierarchical mode)."""
        return "Planner agent operates at plan level, not step level"
    
    def act(self, state: AgentState, reasoning: str) -> Dict[str, Any]:
        """Planner action (not used in hierarchical mode)."""
        return {
            "action": "plan",
            "success": True,
            "result": "Planning complete"
        }


class WorkerAgent(BaseAgent):
    """
    Lower-level Worker Agent (LLM-B).
    
    Responsibilities:
    - Executes localized ReAct loops for current milestone
    - Reports success/failure to Planner
    - Provides detailed error context on failures
    - Focuses on tactical execution
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm_provider: LLMProvider,
        execution_agent: BaseAgent
    ):
        """
        Initialize the worker agent.
        
        Args:
            config: Agent configuration
            llm_provider: LLM provider for reasoning
            execution_agent: Underlying agent for actual execution (e.g., DesktopAutomationAgent)
        """
        super().__init__(config)
        self.llm = llm_provider
        self.execution_agent = execution_agent
        self.current_milestone: Optional[Milestone] = None
        logger.info(f"Initialized WorkerAgent: {config.name}")
    
    def execute_milestone(
        self,
        milestone: Milestone,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single milestone using ReAct loop.
        
        Args:
            milestone: Milestone to execute
            context: Optional execution context
            
        Returns:
            Execution result with success/failure status
        """
        logger.info(f"Worker executing milestone: {milestone.description}")
        
        self.current_milestone = milestone
        milestone.mark_in_progress()
        
        # Create focused task for this milestone
        milestone_task = f"""Milestone: {milestone.description}

Success Criteria: {milestone.success_criteria or 'Complete the milestone objective'}

Context: {context if context else 'None'}

Execute this milestone step by step."""
        
        try:
            # Execute using underlying agent
            result_state = self.execution_agent.run(milestone_task, context)
            
            # Determine if milestone succeeded
            success = self._evaluate_milestone_success(result_state, milestone)
            
            if success:
                milestone.mark_completed()
                logger.info(f"Milestone completed: {milestone.description}")
                
                return {
                    "success": True,
                    "milestone_id": milestone.id,
                    "steps_taken": result_state['current_step'],
                    "result": result_state.get('result')
                }
            else:
                error_msg = result_state.get('error', 'Milestone objectives not met')
                milestone.mark_failed(error_msg)
                logger.warning(f"Milestone failed: {milestone.description} - {error_msg}")
                
                return {
                    "success": False,
                    "milestone_id": milestone.id,
                    "error": error_msg,
                    "steps_taken": result_state['current_step'],
                    "can_retry": milestone.can_retry()
                }
        
        except Exception as e:
            error_msg = f"Worker exception: {str(e)}"
            milestone.mark_failed(error_msg)
            logger.exception(f"Worker failed on milestone: {milestone.description}")
            
            return {
                "success": False,
                "milestone_id": milestone.id,
                "error": error_msg,
                "can_retry": milestone.can_retry()
            }
    
    def _evaluate_milestone_success(
        self,
        result_state: AgentState,
        milestone: Milestone
    ) -> bool:
        """
        Evaluate if milestone was successfully completed.
        
        Args:
            result_state: Final agent state
            milestone: Milestone being evaluated
            
        Returns:
            True if successful, False otherwise
        """
        # Check for errors
        if result_state.get('error'):
            return False
        
        # Check if result indicates success
        if result_state.get('result'):
            result_data = result_state['result']
            if isinstance(result_data, dict):
                if result_data.get('status') == 'completed':
                    return True
        
        # Check if reasonable progress was made
        if result_state['current_step'] > 0:
            # At least some actions were taken
            return True
        
        return False
    
    def reason(self, state: AgentState, observation: str) -> str:
        """Worker reasoning (delegated to execution agent)."""
        return self.execution_agent.reason(state, observation)
    
    def act(self, state: AgentState, reasoning: str) -> Dict[str, Any]:
        """Worker action (delegated to execution agent)."""
        return self.execution_agent.act(state, reasoning)
