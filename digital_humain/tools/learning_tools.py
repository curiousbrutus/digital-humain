"""Learning from Demonstration tools for recording and workflow management."""

from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

from digital_humain.tools.base import BaseTool, ToolMetadata, ToolParameter, ToolResult
from digital_humain.memory.demonstration import DemonstrationMemory
from digital_humain.learning.trajectory_abstraction import TrajectoryAbstractionService
from digital_humain.learning.workflow_definition import WorkflowLibrary


class RecordDemoTool(BaseTool):
    """Tool for recording user demonstrations."""
    
    def __init__(self):
        """Initialize the tool."""
        super().__init__()
        self.demonstration_memory = DemonstrationMemory()
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="record_demo",
            description="Record a user demonstration for learning",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform (start, stop, save)",
                    required=True
                ),
                ToolParameter(
                    name="name",
                    type="string",
                    description="Name for the recording (for 'save' action)",
                    required=False
                ),
                ToolParameter(
                    name="metadata",
                    type="object",
                    description="Optional metadata for the recording",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        action = kwargs.get("action")
        name = kwargs.get("name")
        metadata = kwargs.get("metadata", {})
        
        if not action:
            return ToolResult(
                success=False,
                error="action parameter is required"
            )
        
        try:
            if action == "start":
                self.demonstration_memory.start_recording()
                return ToolResult(
                    success=True,
                    message="Recording started"
                )
            
            elif action == "stop":
                actions = self.demonstration_memory.stop_recording()
                return ToolResult(
                    success=True,
                    data={"action_count": len(actions)},
                    message=f"Recording stopped. Captured {len(actions)} actions"
                )
            
            elif action == "save":
                if not name:
                    return ToolResult(
                        success=False,
                        error="name parameter required for 'save' action"
                    )
                
                actions = self.demonstration_memory.stop_recording()
                self.demonstration_memory.save_demonstration(name, actions, metadata)
                
                return ToolResult(
                    success=True,
                    data={
                        "name": name,
                        "action_count": len(actions)
                    },
                    message=f"Recording saved as '{name}'"
                )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        
        except Exception as e:
            logger.error(f"Recording operation failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class ProcessRecordingTool(BaseTool):
    """Tool for processing recordings into workflows."""
    
    def __init__(self, tas: Optional[TrajectoryAbstractionService] = None):
        """Initialize the tool."""
        super().__init__()
        self.tas = tas or TrajectoryAbstractionService()
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="process_recording",
            description="Process a recording directory into a generalized workflow",
            parameters=[
                ToolParameter(
                    name="recording_dir",
                    type="string",
                    description="Path to recording directory",
                    required=True
                ),
                ToolParameter(
                    name="output_dir",
                    type="string",
                    description="Optional output directory for workflow (defaults to demonstrations/)",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        recording_dir = kwargs.get("recording_dir")
        output_dir = kwargs.get("output_dir", "./demonstrations")
        
        if not recording_dir:
            return ToolResult(
                success=False,
                error="recording_dir parameter is required"
            )
        
        try:
            # Process the recording
            workflow = self.tas.process_recording_directory(recording_dir)
            
            if not workflow:
                return ToolResult(
                    success=False,
                    error="Failed to process recording"
                )
            
            # Save workflow
            output_path = workflow.save(output_dir)
            
            return ToolResult(
                success=True,
                data={
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "steps": len(workflow.steps),
                    "output_path": str(output_path)
                },
                message=f"Workflow '{workflow.name}' created with {len(workflow.steps)} steps"
            )
        
        except Exception as e:
            logger.error(f"Recording processing failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class RegisterWorkflowTool(BaseTool):
    """Tool for registering workflows in the library."""
    
    def __init__(self, library: Optional[WorkflowLibrary] = None):
        """Initialize the tool."""
        super().__init__()
        self.library = library or WorkflowLibrary()
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="register_workflow",
            description="Register a workflow in the workflow library",
            parameters=[
                ToolParameter(
                    name="workflow_path",
                    type="string",
                    description="Path to workflow JSON file",
                    required=True
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        workflow_path = kwargs.get("workflow_path")
        
        if not workflow_path:
            return ToolResult(
                success=False,
                error="workflow_path parameter is required"
            )
        
        try:
            from digital_humain.learning.workflow_definition import WorkflowDefinition
            
            # Load workflow
            workflow = WorkflowDefinition.load(workflow_path)
            
            # Add to library
            output_path = self.library.add_workflow(workflow)
            
            return ToolResult(
                success=True,
                data={
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "path": str(output_path)
                },
                message=f"Workflow '{workflow.name}' registered in library"
            )
        
        except Exception as e:
            logger.error(f"Workflow registration failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class ListWorkflowsTool(BaseTool):
    """Tool for listing workflows in the library."""
    
    def __init__(self, library: Optional[WorkflowLibrary] = None):
        """Initialize the tool."""
        super().__init__()
        self.library = library or WorkflowLibrary()
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="list_workflows",
            description="List workflows in the workflow library",
            parameters=[
                ToolParameter(
                    name="category",
                    type="string",
                    description="Optional category filter",
                    required=False
                ),
                ToolParameter(
                    name="tags",
                    type="array",
                    description="Optional tag filters",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        category = kwargs.get("category")
        tags = kwargs.get("tags")
        
        try:
            workflows = self.library.list_workflows(category=category, tags=tags)
            
            return ToolResult(
                success=True,
                data={"workflows": workflows},
                message=f"Found {len(workflows)} workflows"
            )
        
        except Exception as e:
            logger.error(f"Workflow listing failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class SearchWorkflowsTool(BaseTool):
    """Tool for searching workflows in the library."""
    
    def __init__(self, library: Optional[WorkflowLibrary] = None):
        """Initialize the tool."""
        super().__init__()
        self.library = library or WorkflowLibrary()
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="search_workflows",
            description="Search workflows by name or goal",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query",
                    required=True
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        query = kwargs.get("query")
        
        if not query:
            return ToolResult(
                success=False,
                error="query parameter is required"
            )
        
        try:
            workflows = self.library.search_workflows(query)
            
            return ToolResult(
                success=True,
                data={"workflows": workflows},
                message=f"Found {len(workflows)} matching workflows"
            )
        
        except Exception as e:
            logger.error(f"Workflow search failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )


class GetWorkflowTool(BaseTool):
    """Tool for retrieving a specific workflow."""
    
    def __init__(self, library: Optional[WorkflowLibrary] = None):
        """Initialize the tool."""
        super().__init__()
        self.library = library or WorkflowLibrary()
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="get_workflow",
            description="Get a specific workflow by ID",
            parameters=[
                ToolParameter(
                    name="workflow_id",
                    type="string",
                    description="ID of the workflow",
                    required=True
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        workflow_id = kwargs.get("workflow_id")
        
        if not workflow_id:
            return ToolResult(
                success=False,
                error="workflow_id parameter is required"
            )
        
        try:
            workflow = self.library.get_workflow(workflow_id)
            
            if not workflow:
                return ToolResult(
                    success=False,
                    error=f"Workflow {workflow_id} not found"
                )
            
            return ToolResult(
                success=True,
                data={"workflow": workflow.model_dump()},
                message=f"Retrieved workflow: {workflow.name}"
            )
        
        except Exception as e:
            logger.error(f"Workflow retrieval failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
