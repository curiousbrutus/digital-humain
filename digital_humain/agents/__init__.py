"""Concrete agent implementations."""

# Lazy imports to avoid GUI dependencies when not needed
def __getattr__(name):
    if name == "DesktopAutomationAgent":
        from digital_humain.agents.automation_agent import DesktopAutomationAgent
        return DesktopAutomationAgent
    elif name == "PlannerAgent":
        from digital_humain.agents.hierarchical_planning import PlannerAgent
        return PlannerAgent
    elif name == "WorkerAgent":
        from digital_humain.agents.hierarchical_planning import WorkerAgent
        return WorkerAgent
    elif name == "Milestone":
        from digital_humain.agents.hierarchical_planning import Milestone
        return Milestone
    elif name == "TaskPlan":
        from digital_humain.agents.hierarchical_planning import TaskPlan
        return TaskPlan
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DesktopAutomationAgent",
    "PlannerAgent",
    "WorkerAgent",
    "Milestone",
    "TaskPlan",
]
