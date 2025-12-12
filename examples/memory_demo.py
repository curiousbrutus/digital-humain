"""
Example demonstrating the memory and recording features.

This example shows how to:
1. Record user demonstrations
2. Replay demonstrations
3. Use episodic memory for learning from past experiences
"""

from digital_humain.memory.demonstration import DemonstrationMemory, RecordedAction
from digital_humain.memory.episodic import EpisodicMemory, MemorySummarizer

def demonstration_example():
    """Example of recording and replaying demonstrations."""
    print("=== Demonstration Memory Example ===\n")
    
    # Initialize demonstration memory
    demo_memory = DemonstrationMemory(storage_path="./demo_recordings")
    
    # Create a sample demonstration (simulating recorded actions)
    sample_actions = [
        RecordedAction(
            timestamp=0.0,
            action_type='mouse_click',
            params={'x': 100, 'y': 200, 'button': 'left', 'pressed': True},
            window_title='Notepad'
        ),
        RecordedAction(
            timestamp=0.5,
            action_type='key_press',
            params={'key': 'h'}
        ),
        RecordedAction(
            timestamp=0.6,
            action_type='key_press',
            params={'key': 'e'}
        ),
        RecordedAction(
            timestamp=0.7,
            action_type='key_press',
            params={'key': 'l'}
        ),
        RecordedAction(
            timestamp=0.8,
            action_type='key_press',
            params={'key': 'l'}
        ),
        RecordedAction(
            timestamp=0.9,
            action_type='key_press',
            params={'key': 'o'}
        )
    ]
    
    # Save demonstration
    demo_memory.save_demonstration(
        name='hello_demo',
        actions=sample_actions,
        metadata={'description': 'Types hello in notepad'}
    )
    print("✓ Saved demonstration 'hello_demo'")
    
    # List demonstrations
    demos = demo_memory.list_demonstrations()
    print(f"\nAvailable demonstrations: {len(demos)}")
    for demo in demos:
        print(f"  - {demo['name']}: {demo['action_count']} actions, {demo['duration']:.2f}s")
    
    # Load and display demonstration
    loaded_demo = demo_memory.load_demonstration('hello_demo')
    print(f"\nLoaded demo '{loaded_demo['name']}':")
    print(f"  Created: {loaded_demo['created_at']}")
    print(f"  Actions: {loaded_demo['action_count']}")
    print(f"  Duration: {loaded_demo['total_duration']:.2f}s")
    
    # Dry run (list actions without executing)
    print("\nDry run of demonstration:")
    results = demo_memory.replay_demonstration(
        'hello_demo',
        dry_run=True,
        safety_pause=False
    )
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['action']}: {result['params']}")
    
    print("\n✓ Demonstration example complete\n")


def episodic_memory_example():
    """Example of using episodic memory for learning."""
    print("=== Episodic Memory Example ===\n")
    
    # Initialize episodic memory
    memory = EpisodicMemory(
        storage_path="./episodic_data",
        max_episodes=100,
        enable_recall=True
    )
    
    # Add some sample episodes
    episodes_data = [
        {
            "observation": "User opened browser and navigated to login page",
            "reasoning": "Need to authenticate to access the dashboard",
            "action": {"type": "click", "target": "login_button"},
            "result": "Login form displayed"
        },
        {
            "observation": "Login form visible with username and email fields",
            "reasoning": "Enter user information to proceed",
            "action": {"type": "type_text", "field": "username", "text": "user@example.com"},
            "result": "Username entered"
        },
        {
            "observation": "Dashboard loaded successfully",
            "reasoning": "Navigate to the reports section",
            "action": {"type": "click", "target": "reports_menu"},
            "result": "Reports page opened"
        },
        {
            "observation": "Reports page showing data table",
            "reasoning": "Export report for analysis",
            "action": {"type": "click", "target": "export_button"},
            "result": "Report downloaded"
        }
    ]
    
    print("Adding episodes to memory...")
    for i, ep_data in enumerate(episodes_data):
        episode = memory.add_episode(**ep_data)
        print(f"  ✓ Episode {i+1} stored: {episode.id}")
    
    # Retrieve relevant episodes
    print("\nRetrieving episodes related to 'login':")
    relevant = memory.retrieve_relevant("login", top_k=2)
    for ep in relevant:
        print(f"  - Episode {ep.id}:")
        print(f"    Observation: {ep.observation[:60]}...")
        print(f"    Action: {ep.action}")
    
    # Get memory statistics
    stats = memory.get_stats()
    print("\nMemory Statistics:")
    print(f"  Total episodes: {stats['total_episodes']}")
    print(f"  Max episodes: {stats['max_episodes']}")
    print(f"  Enabled: {stats['enabled']}")
    
    print("\n✓ Episodic memory example complete\n")


def memory_summarizer_example():
    """Example of using the memory summarizer."""
    print("=== Memory Summarizer Example ===\n")
    
    # Initialize summarizer
    summarizer = MemorySummarizer(max_history=5, summary_cadence=3)
    
    # Simulate agent history
    history = [
        {"action": {"action": "screen_analysis"}, "result": "Found login button"},
        {"action": {"action": "click"}, "result": "Clicked login button"},
        {"action": {"action": "type_text"}, "result": "Entered username"},
        {"action": {"action": "type_text"}, "result": "Entered password"},
        {"action": {"action": "click"}, "result": "Clicked submit"},
        {"action": {"action": "wait"}, "result": "Waiting for page load"},
        {"action": {"action": "screen_analysis"}, "result": "Dashboard visible"},
        {"action": {"action": "click"}, "result": "Clicked menu"},
    ]
    
    print("Processing agent history with summarization...")
    for i, item in enumerate(history):
        if summarizer.should_summarize():
            summary = summarizer.create_summary(history[:i+1])
            print(f"  Step {i+1}: Created summary")
            print(f"    {summary}")
        else:
            print(f"  Step {i+1}: {item['action']['action']}")
    
    # Get compressed history
    compressed = summarizer.get_compressed_history(history)
    print(f"\nCompressed history length: {len(compressed)} (original: {len(history)})")
    print("Compressed items:")
    for i, item in enumerate(compressed):
        if item.get('type') == 'summary':
            print(f"  {i+1}. [SUMMARY] {item['content'][:60]}...")
        else:
            print(f"  {i+1}. {item['action']['action']}")
    
    print("\n✓ Memory summarizer example complete\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Digital Humain - Memory & Recording Features Demo")
    print("="*60 + "\n")
    
    demonstration_example()
    episodic_memory_example()
    memory_summarizer_example()
    
    print("="*60)
    print("All examples completed successfully!")
    print("="*60 + "\n")
