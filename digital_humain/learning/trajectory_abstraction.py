"""Trajectory Abstraction Service (TAS) - Process recordings into Generalized Workflows."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from digital_humain.learning.workflow_definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowAction,
    NarrativeMemory,
    EpisodicMemory
)
from digital_humain.learning.action_recognition import (
    ActionRecognitionEngine,
    RecordingEvent,
    RecognizedAction
)
from digital_humain.core.llm import LLMProvider


class RecordingMetadata(BaseModel):
    """Metadata for a recording."""
    
    name: str
    description: Optional[str] = None
    application: str
    created_at: str
    duration_seconds: float
    event_count: int
    screenshot_count: int = 0
    audio_description: Optional[str] = None


class TrajectoryAbstractionService:
    """
    Trajectory Abstraction Service for converting raw recordings into generalized workflows.
    
    Processes:
    1. Screen recording (MP4/WebM)
    2. Event log (JSON of mouse/keyboard events)
    3. Audio/Text description
    
    Outputs:
    - Workflow Definition Language (WDL) JSON
    - Semantic actions (e.g., click(label="Submit") instead of fixed coordinates)
    - Narrative Memory (the 'why')
    - Episodic Memory (the 'how')
    """
    
    def __init__(
        self,
        action_recognizer: Optional[ActionRecognitionEngine] = None,
        llm_provider: Optional[LLMProvider] = None
    ):
        """
        Initialize the Trajectory Abstraction Service.
        
        Args:
            action_recognizer: Action recognition engine
            llm_provider: LLM for narrative extraction
        """
        self.action_recognizer = action_recognizer or ActionRecognitionEngine()
        self.llm_provider = llm_provider
        
        logger.info("TrajectoryAbstractionService initialized")
    
    def process_recording(
        self,
        recording_path: str,
        events_path: str,
        metadata: RecordingMetadata,
        screenshots_dir: Optional[str] = None
    ) -> WorkflowDefinition:
        """
        Process a recording into a workflow definition.
        
        Args:
            recording_path: Path to video recording (MP4/WebM)
            events_path: Path to events JSON file
            metadata: Recording metadata
            screenshots_dir: Optional directory with extracted screenshots
            
        Returns:
            WorkflowDefinition
        """
        logger.info(f"Processing recording: {metadata.name}")
        
        # Step 1: Load events
        events = self._load_events(events_path)
        logger.info(f"Loaded {len(events)} events")
        
        # Step 2: Recognize actions from events
        recognized_actions = self.action_recognizer.process_recording(events, screenshots_dir)
        logger.info(f"Recognized {len(recognized_actions)} actions")
        
        # Step 3: Group actions into steps
        workflow_steps = self._group_actions_into_steps(recognized_actions)
        logger.info(f"Grouped into {len(workflow_steps)} steps")
        
        # Step 4: Extract narrative memory (the 'why')
        narrative_memory = self._extract_narrative_memory(metadata, workflow_steps)
        
        # Step 5: Extract episodic memory (the 'how')
        episodic_memory = self._extract_episodic_memory(metadata, workflow_steps)
        
        # Step 6: Create workflow definition
        workflow = WorkflowDefinition.create(
            name=metadata.name,
            narrative_memory=narrative_memory,
            episodic_memory=episodic_memory,
            steps=workflow_steps,
            category="recorded",
            difficulty="medium",
            estimated_duration_seconds=metadata.duration_seconds,
            tags=["recorded", "lfd"],
            author="user"
        )
        
        logger.info(f"Created workflow definition: {workflow.id}")
        return workflow
    
    def process_recording_directory(
        self,
        recording_dir: str
    ) -> Optional[WorkflowDefinition]:
        """
        Process a recording directory with standard structure.
        
        Expected structure:
        recording_dir/
            video.mp4 (or video.webm)
            events.json
            metadata.json
            screenshots/ (optional)
                frame_0.png
                frame_1.png
                ...
        
        Args:
            recording_dir: Path to recording directory
            
        Returns:
            WorkflowDefinition or None if processing fails
        """
        recording_dir = Path(recording_dir)
        
        if not recording_dir.exists():
            logger.error(f"Recording directory not found: {recording_dir}")
            return None
        
        # Find video file
        video_file = None
        for ext in ['.mp4', '.webm', '.avi']:
            candidates = list(recording_dir.glob(f"*{ext}"))
            if candidates:
                video_file = candidates[0]
                break
        
        if not video_file:
            logger.error(f"No video file found in {recording_dir}")
            return None
        
        # Find events file
        events_file = recording_dir / "events.json"
        if not events_file.exists():
            logger.error(f"Events file not found: {events_file}")
            return None
        
        # Load metadata
        metadata_file = recording_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata_data = json.load(f)
            metadata = RecordingMetadata(**metadata_data)
        else:
            # Create default metadata
            metadata = RecordingMetadata(
                name=recording_dir.name,
                description=f"Recording from {recording_dir.name}",
                application="Unknown",
                created_at=datetime.now().isoformat(),
                duration_seconds=0.0,
                event_count=0
            )
        
        # Check for screenshots directory
        screenshots_dir = recording_dir / "screenshots"
        screenshots_path = str(screenshots_dir) if screenshots_dir.exists() else None
        
        # Process recording
        try:
            workflow = self.process_recording(
                recording_path=str(video_file),
                events_path=str(events_file),
                metadata=metadata,
                screenshots_dir=screenshots_path
            )
            return workflow
        
        except Exception as e:
            logger.exception(f"Failed to process recording: {e}")
            return None
    
    def _load_events(self, events_path: str) -> List[RecordingEvent]:
        """Load events from JSON file."""
        with open(events_path, 'r') as f:
            events_data = json.load(f)
        
        events = []
        for event_data in events_data:
            event = RecordingEvent(**event_data)
            events.append(event)
        
        return events
    
    def _group_actions_into_steps(
        self,
        actions: List[RecognizedAction]
    ) -> List[WorkflowStep]:
        """
        Group recognized actions into logical workflow steps.
        
        Uses heuristics like time gaps and action sequences.
        """
        if not actions:
            return []
        
        steps = []
        current_step_actions = []
        current_step_start = actions[0].timestamp
        
        TIME_GAP_THRESHOLD = 3.0  # seconds - actions separated by this are in different steps
        
        for i, action in enumerate(actions):
            # Check if we should start a new step
            should_start_new_step = False
            
            if current_step_actions:
                time_since_last = action.timestamp - actions[i - 1].timestamp
                
                # Start new step if significant time gap
                if time_since_last > TIME_GAP_THRESHOLD:
                    should_start_new_step = True
                
                # Start new step if action context changed significantly
                elif action.context != actions[i - 1].context:
                    should_start_new_step = True
            
            if should_start_new_step and current_step_actions:
                # Finalize current step
                step = self._create_workflow_step(
                    step_number=len(steps) + 1,
                    actions=current_step_actions
                )
                steps.append(step)
                
                # Start new step
                current_step_actions = [action]
                current_step_start = action.timestamp
            else:
                current_step_actions.append(action)
        
        # Finalize last step
        if current_step_actions:
            step = self._create_workflow_step(
                step_number=len(steps) + 1,
                actions=current_step_actions
            )
            steps.append(step)
        
        return steps
    
    def _create_workflow_step(
        self,
        step_number: int,
        actions: List[RecognizedAction]
    ) -> WorkflowStep:
        """Create a workflow step from recognized actions."""
        # Convert recognized actions to workflow actions
        workflow_actions = self.action_recognizer.convert_to_workflow_actions(actions)
        
        # Generate step description
        description = self._generate_step_description(actions)
        
        # Calculate average confidence
        avg_confidence = sum(a.confidence for a in actions) / len(actions)
        
        # Extract preconditions and postconditions (simplified)
        preconditions = self._extract_preconditions(actions)
        postconditions = self._extract_postconditions(actions)
        
        return WorkflowStep(
            step_number=step_number,
            description=description,
            actions=workflow_actions,
            preconditions=preconditions,
            postconditions=postconditions,
            confidence=avg_confidence,
            metadata={
                "action_count": len(actions),
                "duration": actions[-1].timestamp - actions[0].timestamp if len(actions) > 1 else 0
            }
        )
    
    def _generate_step_description(self, actions: List[RecognizedAction]) -> str:
        """Generate a human-readable description for a step."""
        if not actions:
            return "Empty step"
        
        # Use LLM if available for better descriptions
        if self.llm_provider:
            return self._generate_llm_description(actions)
        
        # Fallback to rule-based description
        primary_action = actions[0]
        
        if primary_action.action_type.value == "type" and primary_action.target_label:
            return f"Enter text in {primary_action.target_label}"
        elif primary_action.action_type.value == "click" and primary_action.target_label:
            return f"Click {primary_action.target_label}"
        elif primary_action.action_type.value == "navigate":
            return "Navigate to page"
        else:
            return f"Perform {primary_action.action_type.value} action"
    
    def _generate_llm_description(self, actions: List[RecognizedAction]) -> str:
        """Use LLM to generate a step description."""
        # Create a prompt describing the actions
        actions_summary = "\n".join([
            f"- {a.action_type.value} on '{a.target_label}' (value: {a.value})"
            for a in actions[:5]  # Limit to first 5 actions
        ])
        
        prompt = f"""Summarize the following user actions into a single, concise step description:

{actions_summary}

Provide a clear, natural language description (max 10 words)."""
        
        try:
            response = self.llm_provider.generate(prompt)
            return response.strip() if response else self._generate_step_description(actions)
        except Exception as e:
            logger.warning(f"LLM description generation failed: {e}")
            return f"Perform {actions[0].action_type.value} action"
    
    def _extract_preconditions(self, actions: List[RecognizedAction]) -> List[str]:
        """Extract preconditions for a step."""
        preconditions = []
        
        # Check if first action requires a specific UI element
        if actions and actions[0].target_label:
            preconditions.append(f"{actions[0].target_label} is visible")
        
        return preconditions
    
    def _extract_postconditions(self, actions: List[RecognizedAction]) -> List[str]:
        """Extract postconditions for a step."""
        postconditions = []
        
        # Check if last action indicates completion
        if actions:
            last_action = actions[-1]
            if last_action.action_type.value == "click" and last_action.target_label:
                if any(keyword in last_action.target_label.lower() for keyword in ["submit", "save", "next"]):
                    postconditions.append("Action completed successfully")
        
        return postconditions
    
    def _extract_narrative_memory(
        self,
        metadata: RecordingMetadata,
        steps: List[WorkflowStep]
    ) -> NarrativeMemory:
        """
        Extract narrative memory (the 'why') from recording.
        
        Uses LLM if available, otherwise uses metadata.
        """
        # Use LLM to extract goal and intent if available
        if self.llm_provider and metadata.description:
            goal, intent = self._extract_goal_and_intent_llm(metadata, steps)
        else:
            # Fallback to metadata-based extraction
            goal = metadata.description or f"Complete workflow: {metadata.name}"
            intent = f"User wants to {metadata.name.lower()}"
        
        # Extract success criteria
        success_criteria = self._extract_success_criteria(steps)
        
        return NarrativeMemory(
            goal=goal,
            user_intent=intent,
            business_context=f"Application: {metadata.application}",
            success_criteria=success_criteria
        )
    
    def _extract_goal_and_intent_llm(
        self,
        metadata: RecordingMetadata,
        steps: List[WorkflowStep]
    ) -> Tuple[str, str]:
        """Use LLM to extract goal and intent."""
        steps_summary = "\n".join([
            f"{i+1}. {step.description}"
            for i, step in enumerate(steps[:10])  # Limit to first 10 steps
        ])
        
        prompt = f"""Analyze this recorded workflow and extract:
1. The high-level goal (what the user wants to accomplish)
2. The user's intent (why they want to do this)

Recording: {metadata.name}
Description: {metadata.description or 'N/A'}
Audio: {metadata.audio_description or 'N/A'}

Steps performed:
{steps_summary}

Provide:
1. Goal: <clear goal statement>
2. Intent: <user intent statement>"""
        
        try:
            response = self.llm_provider.generate(prompt)
            
            # Parse response
            goal = "Unknown goal"
            intent = "Unknown intent"
            
            for line in response.split('\n'):
                if line.startswith('Goal:'):
                    goal = line.replace('Goal:', '').strip()
                elif line.startswith('Intent:'):
                    intent = line.replace('Intent:', '').strip()
            
            return goal, intent
        
        except Exception as e:
            logger.warning(f"LLM goal/intent extraction failed: {e}")
            return metadata.description or f"Complete {metadata.name}", f"User wants to {metadata.name}"
    
    def _extract_success_criteria(self, steps: List[WorkflowStep]) -> List[str]:
        """Extract success criteria from steps."""
        criteria = []
        
        # Check if workflow has postconditions
        for step in steps:
            criteria.extend(step.postconditions)
        
        # Add default criteria
        if not criteria:
            criteria.append("All steps completed without errors")
        
        return list(set(criteria))  # Remove duplicates
    
    def _extract_episodic_memory(
        self,
        metadata: RecordingMetadata,
        steps: List[WorkflowStep]
    ) -> EpisodicMemory:
        """Extract episodic memory (the 'how') from recording."""
        # Extract key UI elements
        key_ui_elements = []
        for step in steps:
            for action in step.actions:
                if action.target and action.target not in key_ui_elements:
                    key_ui_elements.append(action.target)
        
        # Extract timing info
        timing_info = {
            "total_steps": len(steps),
            "total_duration": sum(step.metadata.get('duration', 0) for step in steps),
            "avg_step_duration": sum(step.metadata.get('duration', 0) for step in steps) / len(steps) if steps else 0
        }
        
        # Execution notes
        execution_notes = [
            f"Workflow has {len(steps)} steps",
            f"Uses {len(key_ui_elements)} unique UI elements"
        ]
        
        return EpisodicMemory(
            application=metadata.application,
            environment={
                "recording_date": metadata.created_at,
                "duration": metadata.duration_seconds
            },
            key_ui_elements=key_ui_elements[:20],  # Limit to top 20
            execution_notes=execution_notes,
            timing_info=timing_info
        )
