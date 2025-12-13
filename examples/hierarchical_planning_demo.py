"""
Demonstration of Hierarchical Planning architecture.

This example shows how to use the two-tier agent system:
- Planner Agent: Decomposes tasks into milestones
- Worker Agent: Executes each milestone using ReAct loops

Based on Section III.1: "Achieving Robustness: Hierarchical Planning and ReAct 2.0"
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from digital_humain.core.agent import AgentConfig, AgentRole
from digital_humain.core.llm import OllamaProvider
from digital_humain.agents.hierarchical_planning import (
    PlannerAgent,
    WorkerAgent,
    TaskPlan,
    MilestoneStatus
)
from digital_humain.agents.automation_agent import DesktopAutomationAgent
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.file_tools import FileReadTool, FileWriteTool


def setup_logging():
    """Configure logging for demo."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


def demonstrate_hierarchical_planning():
    """Demonstrate hierarchical planning for a complex task."""
    
    logger.info("=" * 80)
    logger.info("Hierarchical Planning Demonstration")
    logger.info("=" * 80)
    
    # Initialize components
    logger.info("\n[1] Initializing components...")
    
    # LLM for planning
    llm = OllamaProvider(model="llama3:8b-instruct")
    
    # Components for automation
    screen_analyzer = ScreenAnalyzer()
    gui_actions = GUIActions()
    tool_registry = ToolRegistry()
    tool_registry.register(FileReadTool())
    tool_registry.register(FileWriteTool())
    
    # Create base automation agent
    automation_config = AgentConfig(
        name="automation_executor",
        role=AgentRole.EXECUTOR,
        max_iterations=5,  # Limited iterations per milestone
        verbose=False
    )
    
    automation_agent = DesktopAutomationAgent(
        config=automation_config,
        llm_provider=llm,
        screen_analyzer=screen_analyzer,
        gui_actions=gui_actions,
        tool_registry=tool_registry
    )
    
    # Create Planner Agent
    planner_config = AgentConfig(
        name="strategic_planner",
        role=AgentRole.PLANNER,
        temperature=0.3,  # Lower temperature for structured planning
        verbose=True
    )
    
    planner = PlannerAgent(
        config=planner_config,
        llm_provider=llm
    )
    
    # Create Worker Agent
    worker_config = AgentConfig(
        name="tactical_worker",
        role=AgentRole.EXECUTOR,
        temperature=0.7,
        verbose=True
    )
    
    worker = WorkerAgent(
        config=worker_config,
        llm_provider=llm,
        execution_agent=automation_agent
    )
    
    logger.info("✓ Components initialized")
    
    # Define complex task
    task = """
    Prepare a quarterly report:
    1. Open the accounting software
    2. Export the Q3 financial data
    3. Create a summary document
    4. Send the report to the finance team
    """
    
    context = {
        "quarter": "Q3 2024",
        "department": "Finance",
        "sensitivity": "confidential"
    }
    
    logger.info(f"\n[2] Task: {task.strip()}")
    logger.info(f"Context: {context}")
    
    # Phase 1: Planning
    logger.info("\n[3] Phase 1: Strategic Planning")
    logger.info("-" * 80)
    
    try:
        plan = planner.create_plan(task, context)
        
        logger.info(f"\n✓ Plan created with {len(plan.milestones)} milestones:")
        for i, milestone in enumerate(plan.milestones):
            logger.info(f"  {i+1}. {milestone.description}")
            if milestone.success_criteria:
                logger.info(f"     Success: {milestone.success_criteria}")
    
    except Exception as e:
        logger.error(f"✗ Planning failed: {e}")
        return
    
    # Phase 2: Execution
    logger.info("\n[4] Phase 2: Milestone Execution")
    logger.info("-" * 80)
    
    execution_results = []
    
    for i, milestone in enumerate(plan.milestones):
        logger.info(f"\n[Milestone {i+1}/{len(plan.milestones)}] {milestone.description}")
        logger.info("-" * 40)
        
        # Execute milestone
        result = worker.execute_milestone(milestone, context)
        execution_results.append(result)
        
        if result["success"]:
            logger.info(f"✓ Milestone completed in {result['steps_taken']} steps")
            plan.mark_milestone_completed(milestone.id)
        else:
            logger.warning(f"✗ Milestone failed: {result['error']}")
            
            # Check if can retry
            if result.get("can_retry", False):
                logger.info("  Attempting re-planning...")
                
                try:
                    # Re-plan on failure
                    plan = planner.replan_on_failure(
                        plan=plan,
                        failed_milestone=milestone,
                        error_context=result['error']
                    )
                    
                    logger.info(f"✓ Re-planned with {len(plan.milestones)} total milestones")
                    
                    # Retry the milestone with new plan
                    logger.info("  Retrying milestone with new approach...")
                    retry_result = worker.execute_milestone(milestone, context)
                    
                    if retry_result["success"]:
                        logger.info("✓ Retry successful!")
                        plan.mark_milestone_completed(milestone.id)
                        execution_results[-1] = retry_result
                    else:
                        logger.error("✗ Retry also failed, moving to next milestone")
                
                except Exception as e:
                    logger.error(f"✗ Re-planning failed: {e}")
            else:
                logger.error("  Milestone not retryable, aborting task")
                break
    
    # Phase 3: Results Summary
    logger.info("\n[5] Execution Summary")
    logger.info("=" * 80)
    
    total_steps = sum(r.get("steps_taken", 0) for r in execution_results)
    successful = sum(1 for r in execution_results if r["success"])
    
    logger.info(f"Total Milestones: {len(plan.milestones)}")
    logger.info(f"Completed: {successful}/{len(plan.milestones)}")
    logger.info(f"Total Steps: {total_steps}")
    logger.info(f"Overall Success: {plan.is_complete()}")
    
    if plan.is_complete():
        logger.info("\n✓ Task completed successfully!")
    elif plan.has_failed_milestones():
        logger.warning("\n⚠ Task completed with failures")
    else:
        logger.info("\n⚠ Task partially completed")
    
    # Show final milestone statuses
    logger.info("\nFinal Milestone Status:")
    for i, milestone in enumerate(plan.milestones):
        status_icon = "✓" if milestone.status == MilestoneStatus.COMPLETED else "✗"
        logger.info(f"  {status_icon} {milestone.description} - {milestone.status.value}")
        if milestone.error_message:
            logger.info(f"     Error: {milestone.error_message}")


def demonstrate_replan_on_failure():
    """Demonstrate re-planning when a milestone fails."""
    
    logger.info("\n\n" + "=" * 80)
    logger.info("Re-planning Demonstration")
    logger.info("=" * 80)
    
    # Initialize minimal components for demo
    llm = OllamaProvider(model="llama3:8b-instruct")
    
    planner_config = AgentConfig(
        name="replanning_demo",
        role=AgentRole.PLANNER,
        temperature=0.5
    )
    
    planner = PlannerAgent(config=planner_config, llm_provider=llm)
    
    # Create initial plan
    task = "Automate invoice processing from email attachments"
    logger.info(f"\nOriginal Task: {task}")
    
    try:
        plan = planner.create_plan(task, {})
        
        logger.info(f"\nInitial Plan ({len(plan.milestones)} milestones):")
        for i, m in enumerate(plan.milestones):
            logger.info(f"  {i+1}. {m.description}")
        
        # Simulate a failure on second milestone
        if len(plan.milestones) >= 2:
            failed_milestone = plan.milestones[1]
            failed_milestone.mark_in_progress()
            failed_milestone.mark_failed("Unable to locate email attachment folder")
            
            logger.info(f"\n✗ Milestone Failed: {failed_milestone.description}")
            logger.info(f"  Error: {failed_milestone.error_message}")
            
            # Trigger re-planning
            logger.info("\nInitiating re-planning...")
            updated_plan = planner.replan_on_failure(
                plan=plan,
                failed_milestone=failed_milestone,
                error_context=failed_milestone.error_message
            )
            
            logger.info(f"\nUpdated Plan ({len(updated_plan.milestones)} milestones):")
            for i, m in enumerate(updated_plan.milestones):
                status = f"({m.status.value})" if m.status != MilestoneStatus.PENDING else ""
                logger.info(f"  {i+1}. {m.description} {status}")
            
            logger.info("\n✓ Re-planning completed successfully")
    
    except Exception as e:
        logger.error(f"✗ Demo failed: {e}")


def main():
    """Run all demonstrations."""
    setup_logging()
    
    logger.info("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   Hierarchical Planning Architecture Demo                    ║
║                                                                              ║
║  This demonstrates the two-tier agent system for long-horizon tasks:        ║
║  • Planner Agent: Breaks down tasks into milestones                         ║
║  • Worker Agent: Executes milestones with local ReAct loops                 ║
║  • Re-planning: Adapts plan when milestones fail                            ║
║                                                                              ║
║  Based on Section III.1 of the architectural validation document            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Note: These demos will make LLM calls
    # Make sure Ollama is running with llama3:8b-instruct model
    
    try:
        # Demo 1: Full hierarchical planning workflow
        demonstrate_hierarchical_planning()
        
        # Demo 2: Re-planning on failure
        demonstrate_replan_on_failure()
        
    except KeyboardInterrupt:
        logger.info("\n\nDemo interrupted by user")
    except Exception as e:
        logger.exception(f"Demo error: {e}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Demo completed")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
