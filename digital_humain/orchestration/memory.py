"""Shared memory for multi-agent communication."""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime
from loguru import logger


class SharedMemory:
    """
    Shared memory for agent communication and context sharing.
    
    Provides a centralized store for agents to share information,
    similar to Letta's memory architecture.
    """
    
    def __init__(self, persist: bool = False):
        """
        Initialize shared memory.
        
        Args:
            persist: Whether to persist memory to disk (future feature)
        """
        self._memory: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "persist": persist
        }
        logger.info("Initialized SharedMemory")
    
    def set(self, key: str, value: Any, agent_name: Optional[str] = None) -> None:
        """
        Set a value in shared memory.
        
        Args:
            key: Memory key
            value: Value to store
            agent_name: Name of agent setting the value
        """
        self._memory[key] = value
        
        # Record in history
        self._history.append({
            "action": "set",
            "key": key,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "value_type": type(value).__name__
        })
        
        logger.debug(f"Memory set: {key} = {value} (by {agent_name})")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from shared memory.
        
        Args:
            key: Memory key
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        value = self._memory.get(key, default)
        logger.debug(f"Memory get: {key} = {value}")
        return value
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in memory.
        
        Args:
            key: Memory key
            
        Returns:
            True if key exists
        """
        return key in self._memory
    
    def delete(self, key: str, agent_name: Optional[str] = None) -> bool:
        """
        Delete a value from memory.
        
        Args:
            key: Memory key
            agent_name: Name of agent deleting the value
            
        Returns:
            True if deleted, False if key didn't exist
        """
        if key in self._memory:
            del self._memory[key]
            
            self._history.append({
                "action": "delete",
                "key": key,
                "agent": agent_name,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"Memory deleted: {key} (by {agent_name})")
            return True
        
        return False
    
    def update(self, key: str, value: Any, agent_name: Optional[str] = None) -> None:
        """
        Update a value in memory (append if list, merge if dict).
        
        Args:
            key: Memory key
            value: Value to update with
            agent_name: Name of agent updating the value
        """
        if key not in self._memory:
            self.set(key, value, agent_name)
            return
        
        current = self._memory[key]
        
        # Merge based on type
        if isinstance(current, list) and isinstance(value, list):
            current.extend(value)
        elif isinstance(current, dict) and isinstance(value, dict):
            current.update(value)
        else:
            self._memory[key] = value
        
        self._history.append({
            "action": "update",
            "key": key,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.debug(f"Memory updated: {key} (by {agent_name})")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all memory contents.
        
        Returns:
            Dictionary of all memory
        """
        return self._memory.copy()
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get memory operation history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of history entries
        """
        if limit:
            return self._history[-limit:]
        return self._history.copy()
    
    def clear(self, agent_name: Optional[str] = None) -> None:
        """
        Clear all memory.
        
        Args:
            agent_name: Name of agent clearing memory
        """
        count = len(self._memory)
        self._memory.clear()
        
        self._history.append({
            "action": "clear",
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "cleared_items": count
        })
        
        logger.info(f"Memory cleared: {count} items (by {agent_name})")
    
    def snapshot(self) -> Dict[str, Any]:
        """
        Create a snapshot of current memory state.
        
        Returns:
            Snapshot dictionary
        """
        return {
            "memory": self._memory.copy(),
            "history_count": len(self._history),
            "metadata": self._metadata.copy(),
            "timestamp": datetime.now().isoformat()
        }
    
    def stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_keys": len(self._memory),
            "history_entries": len(self._history),
            "memory_size_bytes": len(json.dumps(self._memory)),
            "created_at": self._metadata["created_at"]
        }
