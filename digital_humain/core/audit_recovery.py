"""Audit & Recovery Engine (ARE) for reasoning chain logging and state checkpoints."""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger


class ReasoningLog(BaseModel):
    """A single reasoning chain log entry."""
    
    id: str
    timestamp: float
    step: int
    observation: str
    reasoning: str
    action: Dict[str, Any]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        step: int,
        observation: str,
        reasoning: str,
        action: Dict[str, Any],
        confidence: float = 1.0,
        result: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> "ReasoningLog":
        """Create a new reasoning log entry."""
        content = f"{step}{observation}{reasoning}{json.dumps(action)}"
        log_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        return cls(
            id=log_id,
            timestamp=datetime.now().timestamp(),
            step=step,
            observation=observation,
            reasoning=reasoning,
            action=action,
            confidence=confidence,
            result=result,
            error=error,
            metadata=metadata or {}
        )


class StateCheckpoint(BaseModel):
    """State checkpoint for recovery."""
    
    id: str
    timestamp: float
    task: str
    step: int
    state_snapshot: Dict[str, Any]
    reasoning_logs: List[str]  # IDs of reasoning logs up to this point
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        task: str,
        step: int,
        state_snapshot: Dict[str, Any],
        reasoning_logs: List[str],
        metadata: Optional[Dict] = None
    ) -> "StateCheckpoint":
        """Create a new state checkpoint."""
        content = f"{task}{step}{json.dumps(state_snapshot)}"
        checkpoint_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        return cls(
            id=checkpoint_id,
            timestamp=datetime.now().timestamp(),
            task=task,
            step=step,
            state_snapshot=state_snapshot,
            reasoning_logs=reasoning_logs,
            metadata=metadata or {}
        )


class AuditRecoveryEngine:
    """
    Audit & Recovery Engine for robust error handling and state management.
    
    Features:
    - Reasoning chain logging for every action
    - State checkpoints at sub-task completion
    - Context-aware retry with error state feedback
    - Recovery from failures
    """
    
    def __init__(
        self,
        storage_path: str = "./audit_logs",
        checkpoint_cadence: int = 5,
        max_logs: int = 10000,
        enable_checkpoints: bool = True
    ):
        """
        Initialize the Audit & Recovery Engine.
        
        Args:
            storage_path: Directory to store audit logs and checkpoints
            checkpoint_cadence: Create checkpoint every N steps
            max_logs: Maximum number of logs to retain
            enable_checkpoints: Whether to enable checkpointing
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.checkpoint_cadence = checkpoint_cadence
        self.max_logs = max_logs
        self.enable_checkpoints = enable_checkpoints
        
        # In-memory storage
        self.reasoning_logs: List[ReasoningLog] = []
        self.checkpoints: List[StateCheckpoint] = []
        
        # Create subdirectories
        self.logs_dir = self.storage_path / "logs"
        self.checkpoints_dir = self.storage_path / "checkpoints"
        self.logs_dir.mkdir(exist_ok=True)
        self.checkpoints_dir.mkdir(exist_ok=True)
        
        logger.info(f"AuditRecoveryEngine initialized at {self.storage_path}")
        logger.info(f"Checkpointing: {'enabled' if enable_checkpoints else 'disabled'} (cadence: {checkpoint_cadence})")
    
    def log_reasoning(
        self,
        step: int,
        observation: str,
        reasoning: str,
        action: Dict[str, Any],
        confidence: float = 1.0,
        result: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ReasoningLog:
        """
        Log a reasoning chain entry.
        
        Args:
            step: Current execution step
            observation: What was observed
            reasoning: Chain-of-thought reasoning
            action: Action taken
            confidence: Confidence score (0.0 to 1.0)
            result: Result of the action
            error: Error message if failed
            metadata: Optional metadata
            
        Returns:
            Created ReasoningLog
        """
        log_entry = ReasoningLog.create(
            step=step,
            observation=observation,
            reasoning=reasoning,
            action=action,
            confidence=confidence,
            result=result,
            error=error,
            metadata=metadata
        )
        
        self.reasoning_logs.append(log_entry)
        
        # Enforce max logs limit
        if len(self.reasoning_logs) > self.max_logs:
            removed = self.reasoning_logs.pop(0)
            logger.debug(f"Removed oldest reasoning log {removed.id} (max limit reached)")
        
        # Persist to disk
        self._persist_log(log_entry)
        
        logger.debug(f"Logged reasoning for step {step} (confidence: {confidence:.2f})")
        return log_entry
    
    def create_checkpoint(
        self,
        task: str,
        step: int,
        state_snapshot: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> Optional[StateCheckpoint]:
        """
        Create a state checkpoint.
        
        Args:
            task: Current task description
            step: Current execution step
            state_snapshot: Full state snapshot
            metadata: Optional metadata
            
        Returns:
            Created StateCheckpoint or None if checkpointing disabled
        """
        if not self.enable_checkpoints:
            return None
        
        # Get IDs of all reasoning logs up to this point
        log_ids = [log.id for log in self.reasoning_logs if log.step <= step]
        
        checkpoint = StateCheckpoint.create(
            task=task,
            step=step,
            state_snapshot=state_snapshot,
            reasoning_logs=log_ids,
            metadata=metadata
        )
        
        self.checkpoints.append(checkpoint)
        
        # Persist to disk
        self._persist_checkpoint(checkpoint)
        
        logger.info(f"Checkpoint created at step {step} (ID: {checkpoint.id})")
        return checkpoint
    
    def should_checkpoint(self, step: int) -> bool:
        """
        Determine if a checkpoint should be created at this step.
        
        Args:
            step: Current execution step
            
        Returns:
            True if checkpoint should be created
        """
        if not self.enable_checkpoints:
            return False
        return step > 0 and step % self.checkpoint_cadence == 0
    
    def get_recovery_context(
        self,
        error: str,
        recent_steps: int = 3
    ) -> Dict[str, Any]:
        """
        Get context for error recovery.
        
        Args:
            error: Error message
            recent_steps: Number of recent steps to include
            
        Returns:
            Recovery context dictionary
        """
        # Get recent reasoning logs
        recent_logs = self.reasoning_logs[-recent_steps:] if len(self.reasoning_logs) >= recent_steps else self.reasoning_logs
        
        # Get last checkpoint
        last_checkpoint = self.checkpoints[-1] if self.checkpoints else None
        
        recovery_context = {
            "error": error,
            "recent_reasoning": [
                {
                    "step": log.step,
                    "reasoning": log.reasoning,
                    "action": log.action,
                    "confidence": log.confidence,
                    "result": log.result
                }
                for log in recent_logs
            ],
            "last_checkpoint": {
                "id": last_checkpoint.id,
                "step": last_checkpoint.step,
                "task": last_checkpoint.task
            } if last_checkpoint else None,
            "total_reasoning_logs": len(self.reasoning_logs)
        }
        
        logger.debug(f"Generated recovery context with {len(recent_logs)} recent logs")
        return recovery_context
    
    def get_checkpoint(self, checkpoint_id: Optional[str] = None) -> Optional[StateCheckpoint]:
        """
        Get a checkpoint by ID or the latest checkpoint.
        
        Args:
            checkpoint_id: Optional checkpoint ID (if None, returns latest)
            
        Returns:
            StateCheckpoint or None if not found
        """
        if not self.checkpoints:
            return None
        
        if checkpoint_id is None:
            return self.checkpoints[-1]
        
        for checkpoint in reversed(self.checkpoints):
            if checkpoint.id == checkpoint_id:
                return checkpoint
        
        logger.warning(f"Checkpoint {checkpoint_id} not found")
        return None
    
    def get_reasoning_logs(
        self,
        start_step: Optional[int] = None,
        end_step: Optional[int] = None
    ) -> List[ReasoningLog]:
        """
        Get reasoning logs within a step range.
        
        Args:
            start_step: Start step (inclusive), None for beginning
            end_step: End step (inclusive), None for end
            
        Returns:
            List of ReasoningLog entries
        """
        filtered = self.reasoning_logs
        
        if start_step is not None:
            filtered = [log for log in filtered if log.step >= start_step]
        
        if end_step is not None:
            filtered = [log for log in filtered if log.step <= end_step]
        
        return filtered
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the audit engine."""
        avg_confidence = (
            sum(log.confidence for log in self.reasoning_logs) / len(self.reasoning_logs)
            if self.reasoning_logs else 0.0
        )
        
        error_count = sum(1 for log in self.reasoning_logs if log.error)
        
        return {
            "total_logs": len(self.reasoning_logs),
            "total_checkpoints": len(self.checkpoints),
            "average_confidence": avg_confidence,
            "error_count": error_count,
            "storage_path": str(self.storage_path),
            "checkpointing_enabled": self.enable_checkpoints,
            "checkpoint_cadence": self.checkpoint_cadence
        }
    
    def clear(self, confirm: bool = False) -> None:
        """
        Clear all logs and checkpoints.
        
        Args:
            confirm: Must be True to actually clear
        """
        if not confirm:
            logger.warning("Clear requires confirm=True")
            return
        
        log_count = len(self.reasoning_logs)
        checkpoint_count = len(self.checkpoints)
        
        self.reasoning_logs.clear()
        self.checkpoints.clear()
        
        # Clear storage
        for file in self.logs_dir.glob("log_*.json"):
            file.unlink()
        for file in self.checkpoints_dir.glob("checkpoint_*.json"):
            file.unlink()
        
        logger.info(f"Cleared {log_count} logs and {checkpoint_count} checkpoints")
    
    def _persist_log(self, log: ReasoningLog) -> None:
        """Persist a reasoning log to disk."""
        filepath = self.logs_dir / f"log_{log.id}.json"
        with open(filepath, 'w') as f:
            json.dump(log.model_dump(), f, indent=2)
    
    def _persist_checkpoint(self, checkpoint: StateCheckpoint) -> None:
        """Persist a checkpoint to disk."""
        filepath = self.checkpoints_dir / f"checkpoint_{checkpoint.id}.json"
        with open(filepath, 'w') as f:
            json.dump(checkpoint.model_dump(), f, indent=2)
