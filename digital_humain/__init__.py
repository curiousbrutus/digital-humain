"""
Digital Humain - Self-Hosted Agentic AI for Enterprise Desktop Automation

A Python-based agentic AI framework that combines:
- LangGraph for agent orchestration
- VLM (Vision Language Model) for GUI interaction
- Multi-agent orchestration for complex tasks
- Local LLM integration (Ollama/vLLM) for data privacy
- Unstructured data handling and multi-step reasoning
"""

__version__ = "0.1.0"
__author__ = "Digital Humain Team"

from digital_humain.core.agent import BaseAgent, AgentState
from digital_humain.core.engine import AgentEngine

__all__ = [
    "BaseAgent",
    "AgentState",
    "AgentEngine",
]
