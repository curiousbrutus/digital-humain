"""Episodic memory for enhanced recall and learning."""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger


class Episode(BaseModel):
    """A single episode in episodic memory."""
    
    id: str
    timestamp: float
    observation: str
    reasoning: str
    action: Dict[str, Any]
    result: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(cls, observation: str, reasoning: str, action: Dict[str, Any], 
               result: Optional[str] = None, metadata: Optional[Dict] = None) -> "Episode":
        """Create a new episode with auto-generated ID."""
        content = f"{observation}{reasoning}{json.dumps(action)}"
        episode_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        return cls(
            id=episode_id,
            timestamp=datetime.now().timestamp(),
            observation=observation,
            reasoning=reasoning,
            action=action,
            result=result,
            metadata=metadata or {}
        )


class MemorySummarizer:
    """Summarizes agent history to prevent prompt bloat."""
    
    def __init__(self, max_history: int = 10, summary_cadence: int = 5):
        """
        Initialize memory summarizer.
        
        Args:
            max_history: Maximum number of history items to keep in full detail
            summary_cadence: Summarize every N steps
        """
        self.max_history = max_history
        self.summary_cadence = summary_cadence
        self.step_count = 0
        self.summaries: List[str] = []
        logger.info(f"MemorySummarizer initialized (max={max_history}, cadence={summary_cadence})")
    
    def should_summarize(self) -> bool:
        """Check if it's time to create a summary."""
        self.step_count += 1
        return self.step_count % self.summary_cadence == 0
    
    def create_summary(self, history: List[Dict[str, Any]]) -> str:
        """
        Create a summary from history items.
        
        Args:
            history: List of history items to summarize
            
        Returns:
            Summary string
        """
        if not history:
            return "No actions taken yet."
        
        # Simple summarization (can be enhanced with LLM)
        summary_parts = []
        for i, item in enumerate(history[-self.summary_cadence:]):
            action_type = item.get('action', {}).get('action', 'unknown')
            summary_parts.append(f"Step {i+1}: {action_type}")
        
        summary = f"Summary of last {len(summary_parts)} steps: " + ", ".join(summary_parts)
        self.summaries.append(summary)
        
        logger.debug(f"Created summary: {summary}")
        return summary
    
    def get_compressed_history(self, full_history: List[Dict[str, Any]]) -> List[Any]:
        """
        Get compressed history with summaries for older items.
        
        Args:
            full_history: Complete history list
            
        Returns:
            Compressed history with recent items in full and older items summarized
        """
        if len(full_history) <= self.max_history:
            return full_history
        
        # Keep recent history in full detail
        recent = full_history[-self.max_history:]
        
        # Add summaries for older history
        compressed = []
        if self.summaries:
            compressed.append({"type": "summary", "content": " | ".join(self.summaries)})
        
        compressed.extend(recent)
        return compressed


class EpisodicMemory:
    """
    Episodic memory for storing and retrieving agent experiences.
    
    Stores summarized observations, reasonings, and action snippets in a local store.
    Supports retrieval of top-k relevant items per task.
    """
    
    def __init__(
        self,
        storage_path: str = "./episodic_memory",
        max_episodes: int = 1000,
        enable_recall: bool = True
    ):
        """
        Initialize episodic memory.
        
        Args:
            storage_path: Directory to store episodes
            max_episodes: Maximum number of episodes to retain
            enable_recall: Whether episodic recall is enabled
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_episodes = max_episodes
        self.enable_recall = enable_recall
        
        self.episodes: List[Episode] = []
        self.metadata_file = self.storage_path / "metadata.json"
        
        # Load existing episodes
        self._load_episodes()
        
        # Guardrails
        self.allowed_keys = {"observation", "reasoning", "action", "result", "metadata"}
        self.secret_patterns = ["password", "api_key", "secret", "token", "credential"]
        
        logger.info(f"EpisodicMemory initialized at {self.storage_path}")
        logger.info(f"Loaded {len(self.episodes)} existing episodes")
    
    def add_episode(
        self,
        observation: str,
        reasoning: str,
        action: Dict[str, Any],
        result: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Episode]:
        """
        Add a new episode to memory.
        
        Args:
            observation: What was observed
            reasoning: How the agent reasoned
            action: What action was taken
            result: Result of the action
            metadata: Optional metadata (who, when, etc.)
            
        Returns:
            Created Episode
        """
        if not self.enable_recall:
            logger.debug("Episodic recall disabled, episode not stored")
            return None
        
        # Guardrail: Check for secrets in content
        combined_text = f"{observation} {reasoning} {json.dumps(action)}"
        if self._contains_secrets(combined_text):
            logger.warning("Episode contains potential secrets, not storing")
            return None
        
        # Create episode
        episode = Episode.create(
            observation=observation,
            reasoning=reasoning,
            action=action,
            result=result,
            metadata=metadata or {}
        )
        
        self.episodes.append(episode)
        
        # Enforce max episodes limit
        if len(self.episodes) > self.max_episodes:
            removed = self.episodes.pop(0)
            logger.debug(f"Removed oldest episode {removed.id} (max limit reached)")
        
        # Persist to disk
        self._persist_episode(episode)
        
        logger.debug(f"Added episode {episode.id}")
        return episode
    
    def retrieve_relevant(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Episode]:
        """
        Retrieve top-k relevant episodes for a query.
        
        Args:
            query: Query string to match against
            top_k: Number of episodes to return
            filters: Optional filters (e.g., by metadata)
            
        Returns:
            List of relevant episodes
        """
        if not self.enable_recall or not self.episodes:
            return []
        
        # Simple keyword-based matching (can be enhanced with vector search)
        query_lower = query.lower()
        scored_episodes = []
        
        for episode in self.episodes:
            score = 0
            
            # Check observation
            if query_lower in episode.observation.lower():
                score += 3
            
            # Check reasoning
            if query_lower in episode.reasoning.lower():
                score += 2
            
            # Check action
            action_str = json.dumps(episode.action).lower()
            if query_lower in action_str:
                score += 1
            
            # Apply filters if provided
            if filters:
                matches_filter = all(
                    episode.metadata.get(k) == v for k, v in filters.items()
                )
                if not matches_filter:
                    score = 0
            
            if score > 0:
                scored_episodes.append((score, episode))
        
        # Sort by score and return top-k
        scored_episodes.sort(key=lambda x: x[0], reverse=True)
        top_episodes = [ep for score, ep in scored_episodes[:top_k]]
        
        logger.debug(f"Retrieved {len(top_episodes)} relevant episodes for query: {query}")
        return top_episodes
    
    def get_all_episodes(self) -> List[Episode]:
        """Get all episodes."""
        return self.episodes.copy()
    
    def clear_episodes(self, confirm: bool = False) -> None:
        """
        Clear all episodes (requires confirmation).
        
        Args:
            confirm: Must be True to actually clear
        """
        if not confirm:
            logger.warning("Clear episodes requires confirm=True")
            return
        
        count = len(self.episodes)
        self.episodes.clear()
        
        # Clear storage
        for file in self.storage_path.glob("episode_*.json"):
            file.unlink()
        
        logger.info(f"Cleared {count} episodes from memory")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about episodic memory."""
        return {
            "total_episodes": len(self.episodes),
            "max_episodes": self.max_episodes,
            "enabled": self.enable_recall,
            "storage_path": str(self.storage_path),
            "oldest_episode": self.episodes[0].timestamp if self.episodes else None,
            "newest_episode": self.episodes[-1].timestamp if self.episodes else None
        }
    
    def _contains_secrets(self, text: str) -> bool:
        """Check if text contains potential secrets."""
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in self.secret_patterns)
    
    def _persist_episode(self, episode: Episode) -> None:
        """Persist an episode to disk."""
        filepath = self.storage_path / f"episode_{episode.id}.json"
        with open(filepath, 'w') as f:
            json.dump(episode.model_dump(), f, indent=2)
    
    def _load_episodes(self) -> None:
        """Load episodes from disk."""
        episode_files = sorted(self.storage_path.glob("episode_*.json"))
        
        for filepath in episode_files:
            try:
                with open(filepath, 'r') as f:
                    episode_data = json.load(f)
                    episode = Episode(**episode_data)
                    self.episodes.append(episode)
            except Exception as e:
                logger.error(f"Failed to load episode from {filepath}: {e}")
        
        # Enforce max episodes
        if len(self.episodes) > self.max_episodes:
            excess = len(self.episodes) - self.max_episodes
            self.episodes = self.episodes[excess:]
            logger.info(f"Trimmed {excess} old episodes to enforce max limit")
