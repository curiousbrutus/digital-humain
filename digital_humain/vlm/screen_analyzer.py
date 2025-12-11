"""Screen capture and analysis using VLM."""

import io
import base64
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from PIL import Image, ImageDraw
import pyautogui
from loguru import logger

from digital_humain.core.llm import LLMProvider


class ScreenAnalyzer:
    """
    Analyzes screen content using Vision Language Models.
    
    Provides UI-TARS-like capabilities for understanding and interacting
    with GUI elements.
    """
    
    def __init__(
        self,
        vlm_provider: Optional[LLMProvider] = None,
        save_screenshots: bool = False,
        screenshot_dir: str = "./screenshots"
    ):
        """
        Initialize the screen analyzer.
        
        Args:
            vlm_provider: Vision LLM provider for image analysis
            save_screenshots: Whether to save screenshots for debugging
            screenshot_dir: Directory to save screenshots
        """
        self.vlm_provider = vlm_provider
        self.save_screenshots = save_screenshots
        self.screenshot_dir = Path(screenshot_dir)
        
        if self.save_screenshots:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Disable PyAutoGUI fail-safe for automation
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5  # Add small pause between actions
        
        logger.info("Initialized ScreenAnalyzer")
    
    def capture_screen(
        self,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Image.Image:
        """
        Capture a screenshot of the screen or a specific region.
        
        Args:
            region: Optional (x, y, width, height) tuple for capturing specific region
            
        Returns:
            PIL Image of the screenshot
        """
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            logger.debug(f"Captured screenshot: {screenshot.size}")
            return screenshot
        
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            raise
    
    def save_screenshot(self, image: Image.Image, name: str = "screenshot") -> str:
        """
        Save screenshot to disk.
        
        Args:
            image: PIL Image to save
            name: Base name for the file
            
        Returns:
            Path to saved image
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshot_dir / filename
        
        image.save(filepath)
        logger.info(f"Screenshot saved: {filepath}")
        return str(filepath)
    
    def image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string.
        
        Args:
            image: PIL Image
            
        Returns:
            Base64 encoded string
        """
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def analyze_screen(
        self,
        task: str,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Analyze screen content for a specific task.
        
        Args:
            task: Description of what to look for
            region: Optional screen region to analyze
            
        Returns:
            Analysis results including elements found and suggestions
        """
        # Capture screenshot
        screenshot = self.capture_screen(region)
        
        if self.save_screenshots:
            self.save_screenshot(screenshot, "analysis")
        
        # Analyze with VLM if available
        if self.vlm_provider:
            analysis = self._analyze_with_vlm(screenshot, task)
        else:
            # Fallback to basic OCR-based analysis
            analysis = self._analyze_with_ocr(screenshot, task)
        
        return analysis
    
    def _analyze_with_vlm(self, image: Image.Image, task: str) -> Dict[str, Any]:
        """
        Analyze image using Vision Language Model.
        
        Args:
            image: Screenshot image
            task: Task description
            
        Returns:
            Analysis results
        """
        # Convert image to base64
        img_base64 = self.image_to_base64(image)
        
        # Create prompt for VLM
        prompt = f"""Analyze this screenshot for the following task: {task}

Please identify:
1. Relevant UI elements (buttons, text fields, menus, etc.)
2. Their approximate locations (top-left, center, bottom-right, etc.)
3. Suggested actions to complete the task
4. Any potential issues or warnings

Provide your analysis in a structured format."""
        
        try:
            # Note: This is a simplified version. In practice, you'd need a VLM
            # that can process images, like LLaVA through Ollama
            response = self.vlm_provider.generate_sync(
                prompt=prompt,
                system_prompt="You are a GUI automation assistant that analyzes screenshots."
            )
            
            return {
                "success": True,
                "task": task,
                "image_size": image.size,
                "analysis": response,
                "elements": [],  # Would be extracted from structured response
                "suggestions": []
            }
        
        except Exception as e:
            logger.error(f"VLM analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task,
                "image_size": image.size
            }
    
    def _analyze_with_ocr(self, image: Image.Image, task: str) -> Dict[str, Any]:
        """
        Fallback analysis using OCR.
        
        Args:
            image: Screenshot image
            task: Task description
            
        Returns:
            Basic analysis results
        """
        try:
            import pytesseract
            
            # Extract text from image
            text = pytesseract.image_to_string(image)
            
            # Get text with bounding boxes
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            elements = []
            for i, word in enumerate(data['text']):
                if word.strip():
                    elements.append({
                        'text': word,
                        'confidence': data['conf'][i],
                        'bbox': (
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        )
                    })
            
            return {
                "success": True,
                "task": task,
                "image_size": image.size,
                "text_content": text,
                "elements": elements,
                "analysis": f"Found {len(elements)} text elements on screen.",
                "suggestions": ["Use element coordinates for automation"]
            }
        
        except Exception as e:
            logger.error(f"OCR analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task,
                "image_size": image.size
            }
    
    def find_element(
        self,
        element_description: str,
        confidence: float = 0.8
    ) -> Optional[Tuple[int, int]]:
        """
        Find a UI element on screen by description.
        
        Args:
            element_description: Description of element to find
            confidence: Minimum confidence threshold
            
        Returns:
            (x, y) coordinates of element center, or None if not found
        """
        # Capture and analyze screen
        analysis = self.analyze_screen(f"Find: {element_description}")
        
        if not analysis.get('success'):
            return None
        
        # Look for matching elements
        for element in analysis.get('elements', []):
            # Simple matching - in practice would use more sophisticated matching
            if element_description.lower() in element.get('text', '').lower():
                bbox = element.get('bbox', (0, 0, 0, 0))
                x = bbox[0] + bbox[2] // 2
                y = bbox[1] + bbox[3] // 2
                return (x, y)
        
        logger.warning(f"Element not found: {element_description}")
        return None
    
    def get_screen_info(self) -> Dict[str, Any]:
        """
        Get information about the screen.
        
        Returns:
            Dictionary with screen dimensions and other info
        """
        size = pyautogui.size()
        position = pyautogui.position()
        
        return {
            "screen_size": {"width": size.width, "height": size.height},
            "mouse_position": {"x": position.x, "y": position.y},
            "platform": pyautogui.platform
        }
