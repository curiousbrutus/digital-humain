"""Workflow Definition Language (WDL) for generalized workflows."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger


class ActionType(str, Enum):
    """Types of actions in a workflow."""
    CLICK = "click"
    TYPE = "type"
    PRESS_KEY = "press_key"
    SCROLL = "scroll"
    WAIT = "wait"
    NAVIGATE = "navigate"
    LAUNCH_APP = "launch_app"
    SELECT = "select"
    DRAG = "drag"
    HOVER = "hover"
    VERIFY = "verify"


class WorkflowAction(BaseModel):
    """A single action in a workflow with semantic targeting."""
    
    action_type: ActionType
    target: Optional[str] = None  # Semantic target (e.g., "Submit button", "Email field")
    value: Optional[str] = None  # Value for type actions
    coordinates: Optional[tuple] = None  # Fallback coordinates
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class WorkflowStep(BaseModel):
    """A step in the workflow with context."""
    
    step_number: int
    description: str
    actions: List[WorkflowAction]
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    screenshot_reference: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NarrativeMemory(BaseModel):
    """The 'why' - high-level purpose and intent."""
    
    goal: str
    user_intent: str
    business_context: Optional[str] = None
    success_criteria: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EpisodicMemory(BaseModel):
    """The 'how' - specific execution details."""
    
    application: str
    environment: Dict[str, Any] = Field(default_factory=dict)
    key_ui_elements: List[str] = Field(default_factory=list)
    execution_notes: List[str] = Field(default_factory=list)
    timing_info: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """
    Workflow Definition Language (WDL) for generalized workflows.
    
    Represents a distilled, generalized workflow from demonstrations.
    """
    
    id: str
    name: str
    version: str = "1.0.0"
    created_at: str
    updated_at: str
    
    # Memory components
    narrative_memory: NarrativeMemory
    episodic_memory: EpisodicMemory
    
    # Execution flow
    steps: List[WorkflowStep]
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    difficulty: str = "medium"  # easy, medium, hard
    estimated_duration_seconds: Optional[float] = None
    success_rate: Optional[float] = None
    
    # Access control
    author: Optional[str] = None
    permissions: Dict[str, List[str]] = Field(default_factory=dict)  # ACL
    
    # Versioning
    parent_workflow_id: Optional[str] = None
    changelog: List[str] = Field(default_factory=list)
    
    @classmethod
    def create(
        cls,
        name: str,
        narrative_memory: NarrativeMemory,
        episodic_memory: EpisodicMemory,
        steps: List[WorkflowStep],
        workflow_id: Optional[str] = None,
        **kwargs
    ) -> "WorkflowDefinition":
        """Create a new workflow definition."""
        import hashlib
        
        # Generate ID if not provided
        if workflow_id is None:
            content = f"{name}{narrative_memory.goal}{len(steps)}"
            workflow_id = hashlib.md5(content.encode()).hexdigest()[:16]
        
        now = datetime.now().isoformat()
        
        return cls(
            id=workflow_id,
            name=name,
            created_at=now,
            updated_at=now,
            narrative_memory=narrative_memory,
            episodic_memory=episodic_memory,
            steps=steps,
            **kwargs
        )
    
    def save(self, directory: Union[str, Path]) -> Path:
        """
        Save the workflow definition to a JSON file.
        
        Args:
            directory: Directory to save the workflow
            
        Returns:
            Path to the saved file
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        filename = f"{self.id}_{self.name.replace(' ', '_').lower()}.json"
        filepath = directory / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)
        
        logger.info(f"Workflow '{self.name}' saved to {filepath}")
        return filepath
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "WorkflowDefinition":
        """
        Load a workflow definition from a JSON file.
        
        Args:
            filepath: Path to the workflow file
            
        Returns:
            WorkflowDefinition instance
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Workflow file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        workflow = cls(**data)
        logger.info(f"Workflow '{workflow.name}' loaded from {filepath}")
        return workflow
    
    def update_version(self, change_description: str) -> None:
        """
        Update the workflow version.
        
        Args:
            change_description: Description of changes
        """
        major, minor, patch = map(int, self.version.split('.'))
        patch += 1
        self.version = f"{major}.{minor}.{patch}"
        self.updated_at = datetime.now().isoformat()
        self.changelog.append(f"v{self.version}: {change_description}")
        
        logger.info(f"Workflow version updated to {self.version}")
    
    def add_step(self, step: WorkflowStep, position: Optional[int] = None) -> None:
        """
        Add a step to the workflow.
        
        Args:
            step: WorkflowStep to add
            position: Optional position to insert (None = append)
        """
        if position is None:
            self.steps.append(step)
        else:
            self.steps.insert(position, step)
        
        # Renumber steps
        for i, s in enumerate(self.steps, 1):
            s.step_number = i
        
        self.updated_at = datetime.now().isoformat()
        logger.debug(f"Step added to workflow at position {position or len(self.steps)}")
    
    def remove_step(self, step_number: int) -> bool:
        """
        Remove a step from the workflow.
        
        Args:
            step_number: Step number to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, step in enumerate(self.steps):
            if step.step_number == step_number:
                self.steps.pop(i)
                
                # Renumber remaining steps
                for j, s in enumerate(self.steps, 1):
                    s.step_number = j
                
                self.updated_at = datetime.now().isoformat()
                logger.info(f"Step {step_number} removed from workflow")
                return True
        
        logger.warning(f"Step {step_number} not found in workflow")
        return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "goal": self.narrative_memory.goal,
            "total_steps": len(self.steps),
            "total_actions": sum(len(step.actions) for step in self.steps),
            "tags": self.tags,
            "category": self.category,
            "difficulty": self.difficulty,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the workflow definition.
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        # Check steps are sequential
        expected_step = 1
        for step in self.steps:
            if step.step_number != expected_step:
                errors.append(f"Step numbering gap: expected {expected_step}, got {step.step_number}")
            expected_step += 1
        
        # Check each step has at least one action
        for step in self.steps:
            if not step.actions:
                errors.append(f"Step {step.step_number} has no actions")
        
        # Check actions have valid targets or coordinates
        for step in self.steps:
            for action in step.actions:
                if action.target is None and action.coordinates is None:
                    errors.append(
                        f"Step {step.step_number}: Action {action.action_type} has no target or coordinates"
                    )
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Workflow validation passed")
        else:
            logger.warning(f"Workflow validation failed with {len(errors)} errors")
        
        return is_valid, errors


class WorkflowLibrary:
    """Manages a collection of workflow definitions."""
    
    def __init__(self, storage_path: str = "./demonstrations"):
        """
        Initialize the workflow library.
        
        Args:
            storage_path: Directory to store workflows
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Index of workflows
        self.index: Dict[str, Dict[str, Any]] = {}
        self._build_index()
        
        logger.info(f"WorkflowLibrary initialized at {self.storage_path}")
        logger.info(f"Found {len(self.index)} workflows")
    
    def add_workflow(self, workflow: WorkflowDefinition) -> Path:
        """
        Add a workflow to the library.
        
        Args:
            workflow: WorkflowDefinition to add
            
        Returns:
            Path to saved workflow
        """
        filepath = workflow.save(self.storage_path)
        
        # Update index
        self.index[workflow.id] = workflow.get_summary()
        self._save_index()
        
        return filepath
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            WorkflowDefinition or None if not found
        """
        if workflow_id not in self.index:
            logger.warning(f"Workflow {workflow_id} not found in library")
            return None
        
        # Find the file
        for filepath in self.storage_path.glob(f"{workflow_id}_*.json"):
            return WorkflowDefinition.load(filepath)
        
        logger.error(f"Workflow {workflow_id} in index but file not found")
        return None
    
    def list_workflows(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List workflows in the library.
        
        Args:
            category: Optional category filter
            tags: Optional tag filters (match any)
            
        Returns:
            List of workflow summaries
        """
        workflows = list(self.index.values())
        
        # Filter by category
        if category:
            workflows = [w for w in workflows if w.get('category') == category]
        
        # Filter by tags
        if tags:
            workflows = [
                w for w in workflows
                if any(tag in w.get('tags', []) for tag in tags)
            ]
        
        return sorted(workflows, key=lambda x: x['updated_at'], reverse=True)
    
    def search_workflows(self, query: str) -> List[Dict[str, Any]]:
        """
        Search workflows by name or goal.
        
        Args:
            query: Search query
            
        Returns:
            List of matching workflow summaries
        """
        query_lower = query.lower()
        
        results = [
            summary for summary in self.index.values()
            if query_lower in summary['name'].lower() or query_lower in summary['goal'].lower()
        ]
        
        return sorted(results, key=lambda x: x['updated_at'], reverse=True)
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow from the library.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            True if deleted, False if not found
        """
        if workflow_id not in self.index:
            return False
        
        # Delete file
        for filepath in self.storage_path.glob(f"{workflow_id}_*.json"):
            filepath.unlink()
            logger.info(f"Deleted workflow file: {filepath}")
        
        # Remove from index
        del self.index[workflow_id]
        self._save_index()
        
        return True
    
    def _build_index(self) -> None:
        """Build the workflow index from files."""
        for filepath in self.storage_path.glob("*.json"):
            if filepath.name == "index.json":
                continue
            
            try:
                workflow = WorkflowDefinition.load(filepath)
                self.index[workflow.id] = workflow.get_summary()
            except Exception as e:
                logger.error(f"Failed to load workflow from {filepath}: {e}")
    
    def _save_index(self) -> None:
        """Save the workflow index."""
        index_file = self.storage_path / "index.json"
        with open(index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
