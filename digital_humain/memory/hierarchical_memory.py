"""Hierarchical Memory Manager (HMM) for virtual context paging (MemGPT-style)."""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger


class MemoryPage(BaseModel):
    """A memory page that can be swapped between RAM and disk."""
    
    id: str
    timestamp: float
    content: Dict[str, Any]
    priority: int = Field(default=0, ge=0, le=10)
    access_count: int = 0
    last_accessed: float
    size_bytes: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        content: Dict[str, Any],
        priority: int = 0,
        metadata: Optional[Dict] = None
    ) -> "MemoryPage":
        """Create a new memory page."""
        content_json = json.dumps(content, sort_keys=True)
        page_id = hashlib.md5(content_json.encode()).hexdigest()[:12]
        size = len(content_json.encode('utf-8'))
        
        now = datetime.now().timestamp()
        
        return cls(
            id=page_id,
            timestamp=now,
            content=content,
            priority=priority,
            access_count=0,
            last_accessed=now,
            size_bytes=size,
            metadata=metadata or {}
        )
    
    def access(self) -> None:
        """Record an access to this page."""
        self.access_count += 1
        self.last_accessed = datetime.now().timestamp()


class AgentKnowledgeBase:
    """
    Agent Knowledge Base (AKB) - External storage for paged-out memory.
    
    Supports vector-enabled storage for semantic retrieval.
    """
    
    def __init__(self, storage_path: str = "./agent_knowledge_base"):
        """
        Initialize the Agent Knowledge Base.
        
        Args:
            storage_path: Directory to store the knowledge base
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Index file for quick lookups
        self.index_file = self.storage_path / "index.json"
        self.index: Dict[str, Dict[str, Any]] = self._load_index()
        
        logger.info(f"AgentKnowledgeBase initialized at {self.storage_path}")
        logger.info(f"Loaded {len(self.index)} entries from index")
    
    def store(self, page: MemoryPage) -> None:
        """
        Store a memory page in the knowledge base.
        
        Args:
            page: MemoryPage to store
        """
        filepath = self.storage_path / f"page_{page.id}.json"
        
        with open(filepath, 'w') as f:
            json.dump(page.model_dump(), f, indent=2)
        
        # Update index
        self.index[page.id] = {
            "timestamp": page.timestamp,
            "priority": page.priority,
            "size_bytes": page.size_bytes,
            "access_count": page.access_count,
            "last_accessed": page.last_accessed,
            "metadata": page.metadata
        }
        self._save_index()
        
        logger.debug(f"Stored page {page.id} in AKB ({page.size_bytes} bytes)")
    
    def retrieve(self, page_id: str) -> Optional[MemoryPage]:
        """
        Retrieve a memory page from the knowledge base.
        
        Args:
            page_id: ID of the page to retrieve
            
        Returns:
            MemoryPage or None if not found
        """
        if page_id not in self.index:
            logger.warning(f"Page {page_id} not found in AKB index")
            return None
        
        filepath = self.storage_path / f"page_{page_id}.json"
        
        if not filepath.exists():
            logger.error(f"Page file {filepath} not found (index inconsistency)")
            return None
        
        with open(filepath, 'r') as f:
            page_data = json.load(f)
        
        page = MemoryPage(**page_data)
        logger.debug(f"Retrieved page {page_id} from AKB")
        return page
    
    def delete(self, page_id: str) -> bool:
        """
        Delete a memory page from the knowledge base.
        
        Args:
            page_id: ID of the page to delete
            
        Returns:
            True if deleted, False if not found
        """
        if page_id not in self.index:
            return False
        
        filepath = self.storage_path / f"page_{page_id}.json"
        
        if filepath.exists():
            filepath.unlink()
        
        del self.index[page_id]
        self._save_index()
        
        logger.debug(f"Deleted page {page_id} from AKB")
        return True
    
    def search(
        self,
        query: Optional[str] = None,
        min_priority: Optional[int] = None,
        limit: int = 10
    ) -> List[str]:
        """
        Search for pages in the knowledge base.
        
        Args:
            query: Optional search query (simple keyword matching)
            min_priority: Minimum priority filter
            limit: Maximum number of results
            
        Returns:
            List of page IDs
        """
        results = []
        
        for page_id, metadata in self.index.items():
            # Filter by priority
            if min_priority is not None and metadata['priority'] < min_priority:
                continue
            
            # Simple keyword search if query provided
            if query:
                page = self.retrieve(page_id)
                if page:
                    content_str = json.dumps(page.content).lower()
                    if query.lower() not in content_str:
                        continue
            
            results.append(page_id)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        total_size = sum(meta['size_bytes'] for meta in self.index.values())
        total_accesses = sum(meta['access_count'] for meta in self.index.values())
        
        return {
            "total_pages": len(self.index),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_accesses": total_accesses,
            "storage_path": str(self.storage_path)
        }
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load the index from disk."""
        if not self.index_file.exists():
            return {}
        
        with open(self.index_file, 'r') as f:
            return json.load(f)
    
    def _save_index(self) -> None:
        """Save the index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)


class HierarchicalMemoryManager:
    """
    Hierarchical Memory Manager for virtual context paging.
    
    Implements MemGPT-style memory management with:
    - Main Context: Active prompt window (RAM)
    - External Context: Agent Knowledge Base (Disk)
    - Paging: Dynamic swapping between contexts
    """
    
    def __init__(
        self,
        akb_storage_path: str = "./agent_knowledge_base",
        max_main_context_size: int = 10000,  # ~10K tokens
        page_size: int = 1000  # ~1K tokens per page
    ):
        """
        Initialize the Hierarchical Memory Manager.
        
        Args:
            akb_storage_path: Path to Agent Knowledge Base storage
            max_main_context_size: Maximum size of main context in bytes
            page_size: Target size for memory pages in bytes
        """
        self.akb = AgentKnowledgeBase(akb_storage_path)
        self.max_main_context_size = max_main_context_size
        self.page_size = page_size
        
        # Main context (RAM) - currently active memory
        self.main_context: Dict[str, MemoryPage] = {}
        self.main_context_size = 0
        
        # Track paging operations
        self.page_in_count = 0
        self.page_out_count = 0
        
        logger.info("HierarchicalMemoryManager initialized")
        logger.info(f"Max main context size: {max_main_context_size} bytes")
        logger.info(f"Page size: {page_size} bytes")
    
    def add_to_context(
        self,
        key: str,
        content: Dict[str, Any],
        priority: int = 5,
        metadata: Optional[Dict] = None
    ) -> MemoryPage:
        """
        Add content to the main context.
        
        Args:
            key: Unique key for this content
            content: Content to add
            priority: Priority (0-10, higher = more important)
            metadata: Optional metadata
            
        Returns:
            Created MemoryPage
        """
        page = MemoryPage.create(content, priority, metadata)
        
        # Check if we need to page out before adding
        if self.main_context_size + page.size_bytes > self.max_main_context_size:
            self._auto_page_out()
        
        self.main_context[key] = page
        self.main_context_size += page.size_bytes
        
        logger.debug(f"Added '{key}' to main context ({page.size_bytes} bytes)")
        return page
    
    def get_from_context(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get content from main context.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Content dictionary or None if not found
        """
        if key in self.main_context:
            page = self.main_context[key]
            page.access()
            return page.content
        
        return None
    
    def page_out(self, keys: List[str]) -> int:
        """
        Page out specific keys from main context to AKB.
        
        Args:
            keys: List of keys to page out
            
        Returns:
            Number of pages successfully paged out
        """
        count = 0
        
        for key in keys:
            if key not in self.main_context:
                logger.warning(f"Key '{key}' not in main context, skipping")
                continue
            
            page = self.main_context[key]
            
            # Store in AKB
            self.akb.store(page)
            
            # Remove from main context
            self.main_context_size -= page.size_bytes
            del self.main_context[key]
            
            count += 1
            self.page_out_count += 1
            
            logger.debug(f"Paged out '{key}' to AKB ({page.size_bytes} bytes)")
        
        logger.info(f"Paged out {count} items from main context")
        return count
    
    def page_in(self, page_ids: List[str]) -> int:
        """
        Page in specific pages from AKB to main context.
        
        Args:
            page_ids: List of page IDs to page in
            
        Returns:
            Number of pages successfully paged in
        """
        count = 0
        
        for page_id in page_ids:
            # Retrieve from AKB
            page = self.akb.retrieve(page_id)
            
            if not page:
                logger.warning(f"Page {page_id} not found in AKB")
                continue
            
            # Check if we need to make space
            if self.main_context_size + page.size_bytes > self.max_main_context_size:
                self._auto_page_out()
            
            # Add to main context with generated key
            key = f"paged_in_{page_id}"
            self.main_context[key] = page
            self.main_context_size += page.size_bytes
            
            count += 1
            self.page_in_count += 1
            
            logger.debug(f"Paged in {page_id} to main context ({page.size_bytes} bytes)")
        
        logger.info(f"Paged in {count} items to main context")
        return count
    
    def _auto_page_out(self) -> None:
        """
        Automatically page out items to make space.
        
        Uses LRU-like policy with priority considerations.
        """
        if not self.main_context:
            return
        
        # Sort by: priority (ascending), last_accessed (ascending), access_count (ascending)
        # This prioritizes paging out low priority, least recently accessed, least used items
        sorted_items = sorted(
            self.main_context.items(),
            key=lambda x: (x[1].priority, x[1].last_accessed, x[1].access_count)
        )
        
        # Page out items until we have enough space (target 70% capacity)
        target_size = int(self.max_main_context_size * 0.7)
        keys_to_page_out = []
        size_to_free = 0
        
        for key, page in sorted_items:
            if self.main_context_size - size_to_free <= target_size:
                break
            keys_to_page_out.append(key)
            size_to_free += page.size_bytes
        
        if keys_to_page_out:
            self.page_out(keys_to_page_out)
            logger.info(f"Auto-paged out {len(keys_to_page_out)} items to reach target capacity")
    
    def search_and_page_in(
        self,
        query: str,
        min_priority: Optional[int] = None,
        limit: int = 5
    ) -> List[str]:
        """
        Search AKB and page in relevant items.
        
        Args:
            query: Search query
            min_priority: Minimum priority filter
            limit: Maximum number of items to page in
            
        Returns:
            List of page IDs that were paged in
        """
        # Search AKB
        page_ids = self.akb.search(query, min_priority, limit)
        
        if not page_ids:
            logger.debug(f"No pages found for query: {query}")
            return []
        
        # Page in the results
        self.page_in(page_ids)
        
        return page_ids
    
    def get_main_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the main context."""
        return {
            key: {
                "size_bytes": page.size_bytes,
                "priority": page.priority,
                "access_count": page.access_count,
                "last_accessed": page.last_accessed
            }
            for key, page in self.main_context.items()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory manager."""
        akb_stats = self.akb.get_stats()
        
        return {
            "main_context": {
                "items": len(self.main_context),
                "size_bytes": self.main_context_size,
                "size_mb": self.main_context_size / (1024 * 1024),
                "max_size_bytes": self.max_main_context_size,
                "utilization": self.main_context_size / self.max_main_context_size if self.max_main_context_size > 0 else 0
            },
            "akb": akb_stats,
            "paging": {
                "page_in_count": self.page_in_count,
                "page_out_count": self.page_out_count
            }
        }
    
    def clear_main_context(self, page_out_first: bool = True) -> None:
        """
        Clear the main context.
        
        Args:
            page_out_first: If True, page out items to AKB before clearing
        """
        if page_out_first and self.main_context:
            keys = list(self.main_context.keys())
            self.page_out(keys)
        else:
            self.main_context.clear()
            self.main_context_size = 0
        
        logger.info("Main context cleared")
