"""Concrete agent implementations."""

# Lazy imports to avoid GUI dependencies when not needed
def __getattr__(name):
    if name == "DesktopAutomationAgent":
        from digital_humain.agents.automation_agent import DesktopAutomationAgent
        return DesktopAutomationAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DesktopAutomationAgent",
]
