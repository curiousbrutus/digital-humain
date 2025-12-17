"""Action Recognition Engine - VLM-based UI element detection at event timestamps."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger

from digital_humain.core.llm import LLMProvider
from digital_humain.learning.workflow_definition import ActionType, WorkflowAction


class UIElement(BaseModel):
    """Detected UI element with semantic information."""
    
    label: str
    element_type: str  # button, input, link, checkbox, etc.
    coordinates: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    context: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecordingEvent(BaseModel):
    """A single event from a recording."""
    
    timestamp: float
    event_type: str  # mouse_click, mouse_move, key_press, key_release
    params: Dict[str, Any]
    screenshot_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecognizedAction(BaseModel):
    """An action recognized from events and screen analysis."""
    
    timestamp: float
    action_type: ActionType
    target_element: Optional[UIElement] = None
    target_label: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    context: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionRecognitionEngine:
    """
    Recognizes high-level actions from low-level events using VLM.
    
    Uses OmniParser-like logic to detect UI elements at event timestamps
    and abstract raw events into semantic actions.
    """
    
    def __init__(
        self,
        vlm_provider: Optional[LLMProvider] = None,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize the Action Recognition Engine.
        
        Args:
            vlm_provider: Vision Language Model provider for UI analysis
            confidence_threshold: Minimum confidence for action recognition
        """
        self.vlm_provider = vlm_provider
        self.confidence_threshold = confidence_threshold
        
        logger.info("ActionRecognitionEngine initialized")
        logger.info(f"Confidence threshold: {confidence_threshold}")
    
    def analyze_screenshot(
        self,
        screenshot_path: str,
        coordinates: Optional[Tuple[int, int]] = None
    ) -> List[UIElement]:
        """
        Analyze a screenshot to detect UI elements.
        
        Args:
            screenshot_path: Path to screenshot image
            coordinates: Optional specific coordinates to analyze
            
        Returns:
            List of detected UI elements
        """
        from PIL import Image
        
        screenshot = Image.open(screenshot_path)
        
        if not self.vlm_provider:
            logger.warning("No VLM provider available, using fallback detection")
            return self._fallback_detection(screenshot, coordinates)
        
        # Use VLM to analyze screenshot
        prompt = self._create_analysis_prompt(coordinates)
        
        try:
            # For VLM, we'd pass the image and prompt
            # This is a simplified version
            response = self._query_vlm(screenshot, prompt)
            elements = self._parse_vlm_response(response)
            
            logger.debug(f"Detected {len(elements)} UI elements in screenshot")
            return elements
        
        except Exception as e:
            logger.error(f"VLM analysis failed: {e}, using fallback")
            return self._fallback_detection(screenshot, coordinates)
    
    def recognize_action(
        self,
        event: RecordingEvent,
        screenshot_path: Optional[str] = None
    ) -> Optional[RecognizedAction]:
        """
        Recognize a high-level action from an event.
        
        Args:
            event: Recording event to analyze
            screenshot_path: Optional screenshot at event time
            
        Returns:
            RecognizedAction or None if cannot recognize
        """
        action_type = self._map_event_to_action(event)
        
        if action_type is None:
            return None
        
        # Get UI element at event coordinates if screenshot available
        target_element = None
        target_label = None
        confidence = 0.8  # Default confidence
        
        if screenshot_path and event.params.get('x') and event.params.get('y'):
            coordinates = (event.params['x'], event.params['y'])
            elements = self.analyze_screenshot(screenshot_path, coordinates)
            
            # Find element closest to coordinates
            if elements:
                target_element = self._find_closest_element(elements, coordinates)
                if target_element:
                    target_label = target_element.label
                    confidence = target_element.confidence
        
        # Extract value for type actions
        value = None
        if action_type == ActionType.TYPE:
            value = event.params.get('key') or event.metadata.get('typed_text')
        
        recognized_action = RecognizedAction(
            timestamp=event.timestamp,
            action_type=action_type,
            target_element=target_element,
            target_label=target_label,
            value=value,
            coordinates=(event.params.get('x'), event.params.get('y')) if 'x' in event.params else None,
            confidence=confidence,
            context=self._extract_context(event),
            metadata=event.metadata
        )
        
        logger.debug(f"Recognized action: {action_type} on '{target_label}' (confidence: {confidence:.2f})")
        return recognized_action
    
    def process_recording(
        self,
        events: List[RecordingEvent],
        screenshots_dir: Optional[str] = None
    ) -> List[RecognizedAction]:
        """
        Process a full recording to recognize all actions.
        
        Args:
            events: List of recording events
            screenshots_dir: Optional directory containing timestamped screenshots
            
        Returns:
            List of recognized actions
        """
        logger.info(f"Processing recording with {len(events)} events")
        
        recognized_actions = []
        
        for event in events:
            # Find corresponding screenshot if available
            screenshot_path = None
            if screenshots_dir:
                screenshot_path = self._find_screenshot_for_event(
                    event,
                    Path(screenshots_dir)
                )
            
            # Recognize action
            action = self.recognize_action(event, screenshot_path)
            
            if action and action.confidence >= self.confidence_threshold:
                recognized_actions.append(action)
            else:
                logger.debug(f"Skipping event at {event.timestamp} (low confidence or unrecognized)")
        
        # Filter and merge similar consecutive actions
        recognized_actions = self._merge_similar_actions(recognized_actions)
        
        logger.info(f"Recognized {len(recognized_actions)} actions from recording")
        return recognized_actions
    
    def convert_to_workflow_actions(
        self,
        recognized_actions: List[RecognizedAction]
    ) -> List[WorkflowAction]:
        """
        Convert recognized actions to workflow actions.
        
        Args:
            recognized_actions: List of recognized actions
            
        Returns:
            List of WorkflowAction objects
        """
        workflow_actions = []
        
        for action in recognized_actions:
            workflow_action = WorkflowAction(
                action_type=action.action_type,
                target=action.target_label,
                value=action.value,
                coordinates=action.coordinates,
                metadata={
                    "confidence": action.confidence,
                    "context": action.context,
                    **action.metadata
                }
            )
            workflow_actions.append(workflow_action)
        
        return workflow_actions
    
    def _map_event_to_action(self, event: RecordingEvent) -> Optional[ActionType]:
        """Map an event type to an action type."""
        event_type = event.event_type.lower()
        
        if event_type == 'mouse_click' and event.params.get('pressed'):
            return ActionType.CLICK
        elif event_type == 'key_press':
            key = event.params.get('key', '')
            
            # Check for special keys
            if 'enter' in key.lower():
                return ActionType.PRESS_KEY
            elif 'tab' in key.lower():
                return ActionType.PRESS_KEY
            elif len(key) == 1 or 'Key.' not in key:
                return ActionType.TYPE
            else:
                return ActionType.PRESS_KEY
        
        return None
    
    def _create_analysis_prompt(self, coordinates: Optional[Tuple[int, int]] = None) -> str:
        """Create a prompt for VLM analysis."""
        if coordinates:
            return f"""Analyze this screenshot and identify the UI element at coordinates ({coordinates[0]}, {coordinates[1]}).
            
Provide:
1. Element type (button, input field, link, checkbox, etc.)
2. Element label or text
3. Bounding box coordinates
4. Confidence score (0-1)
5. Surrounding context

Format your response as JSON."""
        else:
            return """Analyze this screenshot and identify all interactive UI elements.

For each element provide:
1. Element type
2. Element label or text  
3. Bounding box coordinates
4. Confidence score (0-1)

Format your response as JSON array."""
    
    def _query_vlm(self, screenshot, prompt: str) -> str:
        """Query the VLM with a screenshot and prompt."""
        # This would use the actual VLM provider
        # For now, return a placeholder response
        logger.debug("Querying VLM for UI analysis")
        
        # In production, this would be:
        # response = self.vlm_provider.generate(prompt, images=[screenshot])
        # return response
        
        return '[]'  # Placeholder
    
    def _parse_vlm_response(self, response: str) -> List[UIElement]:
        """Parse VLM response into UI elements."""
        try:
            elements_data = json.loads(response)
            elements = []
            
            for data in elements_data:
                element = UIElement(
                    label=data.get('label', 'Unknown'),
                    element_type=data.get('type', 'unknown'),
                    coordinates=tuple(data.get('bbox', [0, 0, 0, 0])),
                    confidence=data.get('confidence', 0.5),
                    context=data.get('context')
                )
                elements.append(element)
            
            return elements
        
        except json.JSONDecodeError:
            logger.error("Failed to parse VLM response")
            return []
    
    def _fallback_detection(
        self,
        screenshot,
        coordinates: Optional[Tuple[int, int]] = None
    ) -> List[UIElement]:
        """Fallback UI detection using basic heuristics."""
        # Simple fallback: create a generic element at coordinates
        if coordinates:
            return [
                UIElement(
                    label="UI Element",
                    element_type="unknown",
                    coordinates=(coordinates[0] - 10, coordinates[1] - 10, 20, 20),
                    confidence=0.5,
                    context="Fallback detection"
                )
            ]
        return []
    
    def _find_closest_element(
        self,
        elements: List[UIElement],
        coordinates: Tuple[int, int]
    ) -> Optional[UIElement]:
        """Find the element closest to given coordinates."""
        if not elements:
            return None
        
        x, y = coordinates
        
        def distance(element: UIElement) -> float:
            ex, ey, ew, eh = element.coordinates
            center_x = ex + ew / 2
            center_y = ey + eh / 2
            return ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
        
        return min(elements, key=distance)
    
    def _extract_context(self, event: RecordingEvent) -> str:
        """Extract contextual information from an event."""
        context_parts = []
        
        if event.metadata.get('window_title'):
            context_parts.append(f"Window: {event.metadata['window_title']}")
        
        if event.event_type:
            context_parts.append(f"Event: {event.event_type}")
        
        return " | ".join(context_parts)
    
    def _find_screenshot_for_event(
        self,
        event: RecordingEvent,
        screenshots_dir: Path
    ) -> Optional[str]:
        """Find the screenshot closest to an event timestamp."""
        if not screenshots_dir.exists():
            return None
        
        # Look for screenshots with timestamps
        screenshots = list(screenshots_dir.glob("*.png")) + list(screenshots_dir.glob("*.jpg"))
        
        if not screenshots:
            return None
        
        # Find closest screenshot by timestamp in filename
        # Assuming format: screenshot_<timestamp>.png
        closest = None
        min_diff = float('inf')
        
        for screenshot in screenshots:
            try:
                # Extract timestamp from filename
                # This is a simplified approach
                timestamp_str = screenshot.stem.split('_')[-1]
                timestamp = float(timestamp_str)
                
                diff = abs(timestamp - event.timestamp)
                if diff < min_diff:
                    min_diff = diff
                    closest = screenshot
            except (ValueError, IndexError):
                continue
        
        return str(closest) if closest else None
    
    def _merge_similar_actions(
        self,
        actions: List[RecognizedAction]
    ) -> List[RecognizedAction]:
        """Merge similar consecutive actions (e.g., multiple TYPE events into one)."""
        if not actions:
            return []
        
        merged = []
        current_group = [actions[0]]
        
        for i in range(1, len(actions)):
            current = actions[i]
            previous = actions[i - 1]
            
            # Check if should merge with previous
            should_merge = (
                current.action_type == previous.action_type == ActionType.TYPE and
                current.target_label == previous.target_label and
                current.timestamp - previous.timestamp < 2.0  # Within 2 seconds
            )
            
            if should_merge:
                current_group.append(current)
            else:
                # Finalize current group
                merged_action = self._merge_action_group(current_group)
                merged.append(merged_action)
                current_group = [current]
        
        # Finalize last group
        if current_group:
            merged_action = self._merge_action_group(current_group)
            merged.append(merged_action)
        
        return merged
    
    def _merge_action_group(self, actions: List[RecognizedAction]) -> RecognizedAction:
        """Merge a group of similar actions."""
        if len(actions) == 1:
            return actions[0]
        
        # Merge TYPE actions by concatenating values
        if actions[0].action_type == ActionType.TYPE:
            merged_value = ''.join(a.value or '' for a in actions)
            avg_confidence = sum(a.confidence for a in actions) / len(actions)
            
            return RecognizedAction(
                timestamp=actions[0].timestamp,
                action_type=ActionType.TYPE,
                target_element=actions[0].target_element,
                target_label=actions[0].target_label,
                value=merged_value,
                coordinates=actions[0].coordinates,
                confidence=avg_confidence,
                context=actions[0].context,
                metadata={"merged_from": len(actions)}
            )
        
        # For other action types, just return the first
        return actions[0]
