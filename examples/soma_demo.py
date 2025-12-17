"""
SOMA Architecture Demonstration

This example demonstrates the key components of the SOMA architecture:
1. Orchestration Engine (OE) for task decomposition
2. Hierarchical Memory Manager (HMM) for context paging
3. Audit & Recovery Engine (ARE) for logging and checkpoints
4. Workflow Definition Language (WDL) for learned workflows
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def demo_orchestration_engine():
    """Demonstrate Orchestration Engine capabilities."""
    print("\n" + "="*60)
    print("1. ORCHESTRATION ENGINE (OE) DEMONSTRATION")
    print("="*60)
    
    from digital_humain.core.orchestration_engine import OrchestrationEngine
    from digital_humain.tools.base import ToolRegistry
    
    # Create orchestration engine
    oe = OrchestrationEngine(tool_registry=ToolRegistry())
    
    # Decompose a complex task
    task = "Open browser, navigate to example.com, fill out contact form, and submit"
    print(f"\n📋 Original Task: {task}")
    
    decomposition = oe.decompose_task(task)
    
    print(f"\n✅ Task decomposed into {len(decomposition.subtasks)} subtasks:")
    for i, subtask in enumerate(decomposition.subtasks, 1):
        print(f"   {i}. {subtask.description}")
        print(f"      Role: {subtask.role.value}")
        print(f"      Priority: {subtask.priority.value}")
        print(f"      Tools: {', '.join(subtask.tools_required)}")
    
    print(f"\n📊 Execution Order: {' → '.join(decomposition.execution_order)}")
    print(f"⏱️  Estimated Steps: {decomposition.total_estimated_steps}")
    
    # Get stats
    stats = oe.get_stats()
    print(f"\n📈 OE Stats:")
    print(f"   - Total tools available: {stats['tool_registry']['total_tools']}")
    print(f"   - Subtasks created: {stats['subtasks_created']}")


def demo_hierarchical_memory():
    """Demonstrate Hierarchical Memory Manager capabilities."""
    print("\n" + "="*60)
    print("2. HIERARCHICAL MEMORY MANAGER (HMM) DEMONSTRATION")
    print("="*60)
    
    from digital_humain.memory.hierarchical_memory import HierarchicalMemoryManager
    
    # Create memory manager
    hmm = HierarchicalMemoryManager(
        max_main_context_size=5000,  # 5KB for demo
        page_size=1000
    )
    
    print("\n📝 Adding items to main context...")
    
    # Add items to context
    hmm.add_to_context("task_1", {"description": "Login task", "status": "completed"}, priority=8)
    hmm.add_to_context("task_2", {"description": "Form filling", "status": "in_progress"}, priority=9)
    hmm.add_to_context("task_3", {"description": "Old navigation", "status": "completed"}, priority=3)
    hmm.add_to_context("task_4", {"description": "Data entry", "status": "completed"}, priority=5)
    
    # Get stats
    stats = hmm.get_stats()
    print(f"\n📊 Main Context Stats:")
    print(f"   - Items: {stats['main_context']['items']}")
    print(f"   - Size: {stats['main_context']['size_bytes']} bytes")
    print(f"   - Utilization: {stats['main_context']['utilization']*100:.1f}%")
    
    print(f"\n💾 AKB Stats:")
    print(f"   - Pages: {stats['akb']['total_pages']}")
    print(f"   - Size: {stats['akb']['total_size_mb']:.2f} MB")
    
    # Add large item to trigger paging
    print("\n➕ Adding large item (will trigger auto page-out)...")
    large_content = {"data": "x" * 3000, "type": "large_task"}
    hmm.add_to_context("large_task", large_content, priority=7)
    
    stats = hmm.get_stats()
    print(f"\n📤 After paging:")
    print(f"   - Page-out count: {stats['paging']['page_out_count']}")
    print(f"   - Page-in count: {stats['paging']['page_in_count']}")
    print(f"   - Main context items: {stats['main_context']['items']}")
    print(f"   - AKB pages: {stats['akb']['total_pages']}")
    
    # Search and page in
    print("\n🔍 Searching AKB for 'navigation'...")
    page_ids = hmm.search_and_page_in("navigation", limit=2)
    print(f"   - Paged in {len(page_ids)} items")


def demo_audit_recovery_engine():
    """Demonstrate Audit & Recovery Engine capabilities."""
    print("\n" + "="*60)
    print("3. AUDIT & RECOVERY ENGINE (ARE) DEMONSTRATION")
    print("="*60)
    
    from digital_humain.core.audit_recovery import AuditRecoveryEngine
    
    # Create audit engine
    are = AuditRecoveryEngine(checkpoint_cadence=3)
    
    print("\n📝 Logging reasoning chains...")
    
    # Log several reasoning steps
    steps = [
        {
            "observation": "Login page visible",
            "reasoning": "User needs to authenticate, will enter credentials",
            "action": {"type": "click", "target": "username_field"},
            "confidence": 0.95,
            "result": "Username field focused"
        },
        {
            "observation": "Username field focused",
            "reasoning": "Need to type username",
            "action": {"type": "type", "value": "user@example.com"},
            "confidence": 0.98,
            "result": "Username entered"
        },
        {
            "observation": "Username entered",
            "reasoning": "Now need to enter password",
            "action": {"type": "click", "target": "password_field"},
            "confidence": 0.96,
            "result": "Password field focused"
        },
        {
            "observation": "Password field focused",
            "reasoning": "Type password securely",
            "action": {"type": "type", "value": "********"},
            "confidence": 0.97,
            "result": "Password entered"
        }
    ]
    
    for i, step_data in enumerate(steps, 1):
        are.log_reasoning(
            step=i,
            observation=step_data["observation"],
            reasoning=step_data["reasoning"],
            action=step_data["action"],
            confidence=step_data["confidence"],
            result=step_data["result"]
        )
        
        print(f"   Step {i}: {step_data['observation'][:40]}... (confidence: {step_data['confidence']})")
        
        # Create checkpoint if needed
        if are.should_checkpoint(i):
            are.create_checkpoint(
                task="Login to system",
                step=i,
                state_snapshot={"authenticated": False, "step": i}
            )
            print(f"      ✅ Checkpoint created at step {i}")
    
    # Get stats
    stats = are.get_stats()
    print(f"\n📊 ARE Stats:")
    print(f"   - Total logs: {stats['total_logs']}")
    print(f"   - Total checkpoints: {stats['total_checkpoints']}")
    print(f"   - Average confidence: {stats['average_confidence']:.2f}")
    print(f"   - Error count: {stats['error_count']}")
    
    # Simulate error and get recovery context
    print("\n⚠️  Simulating error and generating recovery context...")
    recovery_ctx = are.get_recovery_context("Login failed - invalid credentials", recent_steps=2)
    
    print(f"\n🔄 Recovery Context:")
    print(f"   - Error: {recovery_ctx['error']}")
    print(f"   - Recent reasoning steps: {len(recovery_ctx['recent_reasoning'])}")
    for r in recovery_ctx['recent_reasoning']:
        print(f"      • Step {r['step']}: {r['reasoning'][:50]}...")


def demo_workflow_definition():
    """Demonstrate Workflow Definition Language."""
    print("\n" + "="*60)
    print("4. WORKFLOW DEFINITION LANGUAGE (WDL) DEMONSTRATION")
    print("="*60)
    
    from digital_humain.learning.workflow_definition import (
        WorkflowDefinition,
        WorkflowStep,
        WorkflowAction,
        ActionType,
        NarrativeMemory,
        EpisodicMemory,
        WorkflowLibrary
    )
    
    print("\n📝 Creating a workflow definition...")
    
    # Create narrative memory (the 'why')
    narrative = NarrativeMemory(
        goal="Authenticate user into the system",
        user_intent="User wants to access their account",
        business_context="E-commerce application login",
        success_criteria=[
            "User is authenticated",
            "Dashboard is visible",
            "Session is created"
        ]
    )
    
    # Create episodic memory (the 'how')
    episodic = EpisodicMemory(
        application="ShopApp v2.1",
        environment={"browser": "Chrome", "os": "Windows"},
        key_ui_elements=["Username field", "Password field", "Login button", "Remember me checkbox"],
        execution_notes=["Workflow is deterministic", "No branching logic"],
        timing_info={"avg_duration": 15.3, "min_duration": 12.1, "max_duration": 18.7}
    )
    
    # Create workflow steps
    steps = [
        WorkflowStep(
            step_number=1,
            description="Enter username",
            actions=[
                WorkflowAction(
                    action_type=ActionType.CLICK,
                    target="Username field"
                ),
                WorkflowAction(
                    action_type=ActionType.TYPE,
                    target="Username field",
                    value="user@example.com"
                )
            ],
            preconditions=["Login page is visible"],
            postconditions=["Username is entered"],
            confidence=0.95
        ),
        WorkflowStep(
            step_number=2,
            description="Enter password",
            actions=[
                WorkflowAction(
                    action_type=ActionType.CLICK,
                    target="Password field"
                ),
                WorkflowAction(
                    action_type=ActionType.TYPE,
                    target="Password field",
                    value="********"
                )
            ],
            preconditions=["Username is entered"],
            postconditions=["Password is entered"],
            confidence=0.96
        ),
        WorkflowStep(
            step_number=3,
            description="Submit login form",
            actions=[
                WorkflowAction(
                    action_type=ActionType.CLICK,
                    target="Login button"
                )
            ],
            preconditions=["Username is entered", "Password is entered"],
            postconditions=["Login successful", "Dashboard visible"],
            confidence=0.98
        )
    ]
    
    # Create workflow definition
    workflow = WorkflowDefinition.create(
        name="Login to ShopApp",
        narrative_memory=narrative,
        episodic_memory=episodic,
        steps=steps,
        category="authentication",
        difficulty="easy",
        tags=["login", "authentication", "ecommerce"],
        author="demo_user"
    )
    
    print(f"\n✅ Workflow Created:")
    print(f"   - ID: {workflow.id}")
    print(f"   - Name: {workflow.name}")
    print(f"   - Version: {workflow.version}")
    print(f"   - Steps: {len(workflow.steps)}")
    
    # Get workflow summary
    summary = workflow.get_summary()
    print(f"\n📊 Workflow Summary:")
    print(f"   - Goal: {summary['goal']}")
    print(f"   - Total actions: {summary['total_actions']}")
    print(f"   - Category: {summary['category']}")
    print(f"   - Difficulty: {summary['difficulty']}")
    print(f"   - Tags: {', '.join(summary['tags'])}")
    
    # Validate workflow
    is_valid, errors = workflow.validate()
    print(f"\n✅ Validation: {'PASSED' if is_valid else 'FAILED'}")
    if errors:
        for error in errors:
            print(f"   ⚠️  {error}")
    
    print("\n📚 Creating workflow library...")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        library = WorkflowLibrary(storage_path=tmpdir)
        
        # Add workflow to library
        saved_path = library.add_workflow(workflow)
        print(f"   ✅ Workflow saved to: {saved_path}")
        
        # List workflows
        workflows = library.list_workflows()
        print(f"\n📋 Workflows in library: {len(workflows)}")
        for wf in workflows:
            print(f"   - {wf['name']} (v{wf['version']}) - {wf['total_steps']} steps")
        
        # Search workflows
        search_results = library.search_workflows("login")
        print(f"\n🔍 Search results for 'login': {len(search_results)} found")


def main():
    """Run all SOMA demonstrations."""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + " "*12 + "SOMA ARCHITECTURE DEMONSTRATION" + " "*15 + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    try:
        demo_orchestration_engine()
        demo_hierarchical_memory()
        demo_audit_recovery_engine()
        demo_workflow_definition()
        
        print("\n" + "="*60)
        print("✨ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nThe SOMA architecture provides:")
        print("  • Modular, scalable design")
        print("  • Hierarchical memory with infinite context")
        print("  • Complete audit trail for debugging")
        print("  • Learning from demonstration capabilities")
        print("  • Semantic workflow definitions")
        print("\nSee docs/SOMA_ARCHITECTURE.md for full documentation")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
