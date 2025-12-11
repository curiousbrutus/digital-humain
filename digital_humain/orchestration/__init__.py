"""Multi-agent orchestration module."""

from digital_humain.orchestration.coordinator import AgentCoordinator
from digital_humain.orchestration.memory import SharedMemory
from digital_humain.orchestration.registry import AgentRegistry

__all__ = [
    "AgentCoordinator",
    "SharedMemory",
    "AgentRegistry",
]
