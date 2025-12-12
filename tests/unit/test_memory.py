"""Unit tests for memory modules."""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Mock pyautogui before importing memory modules
import sys
sys.modules['pyautogui'] = Mock()
sys.modules['pynput'] = Mock()
sys.modules['pynput.mouse'] = Mock()
sys.modules['pynput.keyboard'] = Mock()
sys.modules['pygetwindow'] = Mock()

from digital_humain.memory.demonstration import DemonstrationMemory, RecordedAction
from digital_humain.memory.episodic import EpisodicMemory, Episode, MemorySummarizer


class TestRecordedAction:
    """Test RecordedAction model."""
    
    def test_create_recorded_action(self):
        """Test creating a recorded action."""
        action = RecordedAction(
            timestamp=1.5,
            action_type='mouse_click',
            params={'x': 100, 'y': 200, 'button': 'left'},
            window_title='Test Window',
            screen_size=(1920, 1080)
        )
        
        assert action.timestamp == 1.5
        assert action.action_type == 'mouse_click'
        assert action.params['x'] == 100
        assert action.window_title == 'Test Window'


class TestDemonstrationMemory:
    """Test DemonstrationMemory functionality."""
    
    def test_save_and_load_demonstration(self):
        """Test saving and loading demonstrations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            demo_memory = DemonstrationMemory(storage_path=tmpdir)
            
            # Create test actions
            actions = [
                RecordedAction(
                    timestamp=0.0,
                    action_type='mouse_click',
                    params={'x': 100, 'y': 200}
                ),
                RecordedAction(
                    timestamp=1.0,
                    action_type='key_press',
                    params={'key': 'a'}
                ),
                RecordedAction(
                    timestamp=2.0,
                    action_type='mouse_move',
                    params={'x': 150, 'y': 250}
                )
            ]
            
            # Save demonstration
            demo_memory.save_demonstration(
                name='test_demo',
                actions=actions,
                metadata={'description': 'Test demonstration'}
            )
            
            # Load demonstration
            loaded_demo = demo_memory.load_demonstration('test_demo')
            
            assert loaded_demo is not None
            assert loaded_demo['name'] == 'test_demo'
            assert len(loaded_demo['actions']) == 3
            assert loaded_demo['action_count'] == 3
            assert loaded_demo['metadata']['description'] == 'Test demonstration'
    
    def test_list_demonstrations(self):
        """Test listing demonstrations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            demo_memory = DemonstrationMemory(storage_path=tmpdir)
            
            actions = [
                RecordedAction(timestamp=0.0, action_type='mouse_click', params={})
            ]
            
            # Save multiple demonstrations
            demo_memory.save_demonstration('demo1', actions)
            demo_memory.save_demonstration('demo2', actions)
            demo_memory.save_demonstration('demo3', actions)
            
            # List demonstrations
            demos = demo_memory.list_demonstrations()
            
            assert len(demos) == 3
            assert all('name' in demo for demo in demos)
            assert all('created_at' in demo for demo in demos)
    
    def test_delete_demonstration(self):
        """Test deleting a demonstration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            demo_memory = DemonstrationMemory(storage_path=tmpdir)
            
            actions = [
                RecordedAction(timestamp=0.0, action_type='mouse_click', params={})
            ]
            
            demo_memory.save_demonstration('to_delete', actions)
            
            # Verify it exists
            assert demo_memory.load_demonstration('to_delete') is not None
            
            # Delete it
            result = demo_memory.delete_demonstration('to_delete')
            assert result is True
            
            # Verify it's gone
            assert demo_memory.load_demonstration('to_delete') is None
    
    def test_replay_dry_run(self):
        """Test dry-run replay mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            demo_memory = DemonstrationMemory(storage_path=tmpdir)
            
            actions = [
                RecordedAction(
                    timestamp=0.0,
                    action_type='mouse_click',
                    params={'x': 100, 'y': 200}
                ),
                RecordedAction(
                    timestamp=0.5,
                    action_type='key_press',
                    params={'key': 'enter'}
                )
            ]
            
            demo_memory.save_demonstration('dry_run_test', actions)
            
            # Replay in dry-run mode
            results = demo_memory.replay_demonstration(
                'dry_run_test',
                dry_run=True,
                safety_pause=False
            )
            
            assert len(results) == 2
            assert all(r['dry_run'] for r in results)
            assert results[0]['action'] == 'mouse_click'
            assert results[1]['action'] == 'key_press'


class TestEpisode:
    """Test Episode model."""
    
    def test_create_episode(self):
        """Test creating an episode."""
        episode = Episode.create(
            observation="User clicked button",
            reasoning="Need to submit form",
            action={"type": "click", "x": 100, "y": 200},
            result="Form submitted"
        )
        
        assert episode.id is not None
        assert len(episode.id) == 12
        assert episode.observation == "User clicked button"
        assert episode.reasoning == "Need to submit form"
        assert episode.result == "Form submitted"


class TestMemorySummarizer:
    """Test MemorySummarizer functionality."""
    
    def test_should_summarize(self):
        """Test summary cadence detection."""
        summarizer = MemorySummarizer(summary_cadence=3)
        
        assert not summarizer.should_summarize()  # step 1
        assert not summarizer.should_summarize()  # step 2
        assert summarizer.should_summarize()      # step 3
        assert not summarizer.should_summarize()  # step 4
        assert not summarizer.should_summarize()  # step 5
        assert summarizer.should_summarize()      # step 6
    
    def test_create_summary(self):
        """Test summary creation."""
        summarizer = MemorySummarizer(summary_cadence=3)
        
        history = [
            {"action": {"action": "click"}},
            {"action": {"action": "type"}},
            {"action": {"action": "submit"}}
        ]
        
        summary = summarizer.create_summary(history)
        
        assert "Summary of last 3 steps" in summary
        assert "click" in summary
        assert "type" in summary
        assert "submit" in summary
    
    def test_compressed_history(self):
        """Test history compression."""
        summarizer = MemorySummarizer(max_history=3, summary_cadence=2)
        
        # Create history larger than max
        history = [
            {"action": {"action": f"action_{i}"}} for i in range(10)
        ]
        
        compressed = summarizer.get_compressed_history(history)
        
        # Should have recent items plus summary
        assert len(compressed) <= 4  # 3 recent + 1 summary entry
        
        # Last 3 items should be full detail
        assert compressed[-1] == history[-1]
        assert compressed[-2] == history[-2]
        assert compressed[-3] == history[-3]


class TestEpisodicMemory:
    """Test EpisodicMemory functionality."""
    
    def test_add_episode(self):
        """Test adding an episode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EpisodicMemory(storage_path=tmpdir)
            
            episode = memory.add_episode(
                observation="Screen shows login form",
                reasoning="Need to enter user data",
                action={"type": "type_text", "text": "username"},
                result="Typed username"
            )
            
            assert episode is not None
            assert len(memory.get_all_episodes()) == 1
    
    def test_retrieve_relevant(self):
        """Test retrieving relevant episodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EpisodicMemory(storage_path=tmpdir)
            
            # Add several episodes
            memory.add_episode(
                observation="Login form visible",
                reasoning="Need to login",
                action={"type": "click", "target": "login_button"}
            )
            
            memory.add_episode(
                observation="Dashboard loaded",
                reasoning="Navigate to settings",
                action={"type": "click", "target": "settings_menu"}
            )
            
            memory.add_episode(
                observation="Settings page open",
                reasoning="Need to change password",
                action={"type": "click", "target": "password_field"}
            )
            
            # Retrieve episodes related to "login"
            relevant = memory.retrieve_relevant("login", top_k=2)
            
            assert len(relevant) <= 2
            assert any("login" in ep.observation.lower() for ep in relevant)
    
    def test_max_episodes_limit(self):
        """Test that max episodes limit is enforced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EpisodicMemory(storage_path=tmpdir, max_episodes=5)
            
            # Add more episodes than the limit
            for i in range(10):
                memory.add_episode(
                    observation=f"Observation {i}",
                    reasoning=f"Reasoning {i}",
                    action={"step": i}
                )
            
            # Should only have max_episodes
            assert len(memory.get_all_episodes()) == 5
            
            # Oldest episodes should be removed
            episodes = memory.get_all_episodes()
            assert all(f"Observation {i}" in ep.observation for i, ep in enumerate(episodes, start=5))
    
    def test_secret_filtering(self):
        """Test that episodes with secrets are not stored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EpisodicMemory(storage_path=tmpdir)
            
            # Try to add episode with secret
            episode = memory.add_episode(
                observation="Entered password: my_secret_pass",
                reasoning="Need to authenticate",
                action={"type": "type", "text": "password"}
            )
            
            # Episode should not be stored
            assert episode is None
            assert len(memory.get_all_episodes()) == 0
    
    def test_get_stats(self):
        """Test getting memory statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EpisodicMemory(storage_path=tmpdir, max_episodes=100)
            
            memory.add_episode(
                observation="Test observation",
                reasoning="Test reasoning",
                action={"test": "action"}
            )
            
            stats = memory.get_stats()
            
            assert stats['total_episodes'] == 1
            assert stats['max_episodes'] == 100
            assert stats['enabled'] is True
            assert stats['oldest_episode'] is not None
    
    def test_clear_episodes(self):
        """Test clearing episodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EpisodicMemory(storage_path=tmpdir)
            
            # Add some episodes
            for i in range(5):
                memory.add_episode(
                    observation=f"Observation {i}",
                    reasoning="Test",
                    action={"step": i}
                )
            
            assert len(memory.get_all_episodes()) == 5
            
            # Clear without confirm should not work
            memory.clear_episodes(confirm=False)
            assert len(memory.get_all_episodes()) == 5
            
            # Clear with confirm should work
            memory.clear_episodes(confirm=True)
            assert len(memory.get_all_episodes()) == 0
    
    def test_persist_and_reload(self):
        """Test that episodes persist across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first instance and add episodes
            memory1 = EpisodicMemory(storage_path=tmpdir)
            memory1.add_episode(
                observation="Test observation",
                reasoning="Test reasoning",
                action={"test": "action"}
            )
            
            episode_id = memory1.get_all_episodes()[0].id
            
            # Create second instance - should load existing episodes
            memory2 = EpisodicMemory(storage_path=tmpdir)
            
            assert len(memory2.get_all_episodes()) == 1
            assert memory2.get_all_episodes()[0].id == episode_id
