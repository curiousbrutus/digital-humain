"""Tool caching for ReAct pattern optimization.

Implements the ToolCacheAgent pattern from Section 3.4:
- Caches idempotent tool call results
- Reduces redundant computation in ReAct loops
- Provides up to 1.69x latency speed-up
- Maintains correctness with invalidation rules
"""

import hashlib
import time
from typing import Any, Dict, Optional, Set, Callable
from collections import OrderedDict
from loguru import logger


class CacheEntry:
    """Represents a cached tool result."""
    
    def __init__(
        self,
        key: str,
        result: Any,
        tool_name: str,
        timestamp: float
    ):
        """
        Initialize cache entry.
        
        Args:
            key: Cache key (hash of inputs)
            result: Cached result
            tool_name: Name of tool
            timestamp: Creation timestamp
        """
        self.key = key
        self.result = result
        self.tool_name = tool_name
        self.timestamp = timestamp
        self.access_count = 0
        self.last_access = timestamp
    
    def access(self) -> None:
        """Record cache access."""
        self.access_count += 1
        self.last_access = time.time()
    
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.timestamp


class ToolCache:
    """
    Cache for tool execution results.
    
    Features:
    - LRU eviction policy
    - TTL-based expiration
    - Invalidation rules for stateful operations
    - Statistics tracking
    """
    
    def __init__(
        self,
        max_size: int = 100,
        default_ttl: float = 300.0,  # 5 minutes
        enable_stats: bool = True
    ):
        """
        Initialize tool cache.
        
        Args:
            max_size: Maximum number of cached entries
            default_ttl: Default time-to-live in seconds
            enable_stats: Enable statistics tracking
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats
        
        # Cache storage (ordered for LRU)
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Invalidation rules: tool_name -> set of tools that invalidate it
        self.invalidation_rules: Dict[str, Set[str]] = {}
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'invalidations': 0,
            'total_requests': 0
        }
        
        logger.info(
            f"Initialized ToolCache (max_size={max_size}, ttl={default_ttl}s)"
        )
    
    def _compute_cache_key(
        self,
        tool_name: str,
        args: tuple,
        kwargs: Dict[str, Any]
    ) -> str:
        """
        Compute cache key from tool name and arguments.
        
        Args:
            tool_name: Name of tool
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a stable representation of the call
        call_repr = f"{tool_name}:{args}:{sorted(kwargs.items())}"
        
        # Hash for compact key
        return hashlib.sha256(call_repr.encode()).hexdigest()[:16]
    
    def get(
        self,
        tool_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get cached result for tool call.
        
        Args:
            tool_name: Name of tool
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Cached result or None if not found/expired
        """
        if kwargs is None:
            kwargs = {}
        
        self.stats['total_requests'] += 1
        
        cache_key = self._compute_cache_key(tool_name, args, kwargs)
        
        # Check if in cache
        if cache_key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[cache_key]
        
        # Check TTL
        if entry.age() > self.default_ttl:
            logger.debug(f"Cache entry expired: {tool_name}")
            del self.cache[cache_key]
            self.stats['misses'] += 1
            return None
        
        # Cache hit
        entry.access()
        self.stats['hits'] += 1
        
        # Move to end (most recently used)
        self.cache.move_to_end(cache_key)
        
        logger.debug(
            f"Cache HIT: {tool_name} (age: {entry.age():.1f}s, "
            f"accesses: {entry.access_count})"
        )
        
        return entry.result
    
    def put(
        self,
        tool_name: str,
        result: Any,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store result in cache.
        
        Args:
            tool_name: Name of tool
            result: Result to cache
            args: Positional arguments
            kwargs: Keyword arguments
        """
        if kwargs is None:
            kwargs = {}
        
        cache_key = self._compute_cache_key(tool_name, args, kwargs)
        
        # Check if cache is full
        if len(self.cache) >= self.max_size and cache_key not in self.cache:
            # Evict least recently used
            evicted_key, evicted_entry = self.cache.popitem(last=False)
            self.stats['evictions'] += 1
            logger.debug(f"Cache eviction: {evicted_entry.tool_name}")
        
        # Create and store entry
        entry = CacheEntry(
            key=cache_key,
            result=result,
            tool_name=tool_name,
            timestamp=time.time()
        )
        
        self.cache[cache_key] = entry
        
        logger.debug(f"Cache PUT: {tool_name}")
    
    def invalidate(self, tool_name: str) -> int:
        """
        Invalidate all cache entries for a tool.
        
        Used when tool state changes or after stateful operations.
        
        Args:
            tool_name: Name of tool to invalidate
            
        Returns:
            Number of entries invalidated
        """
        keys_to_remove = [
            key for key, entry in self.cache.items()
            if entry.tool_name == tool_name
        ]
        
        for key in keys_to_remove:
            del self.cache[key]
            self.stats['invalidations'] += 1
        
        if keys_to_remove:
            logger.debug(
                f"Cache invalidation: {tool_name} ({len(keys_to_remove)} entries)"
            )
        
        return len(keys_to_remove)
    
    def invalidate_by_rules(self, tool_name: str) -> int:
        """
        Invalidate cache entries based on invalidation rules.
        
        When a stateful tool is executed, invalidate related cached results.
        
        Args:
            tool_name: Name of tool that was executed
            
        Returns:
            Number of entries invalidated
        """
        if tool_name not in self.invalidation_rules:
            return 0
        
        total_invalidated = 0
        
        for invalidated_tool in self.invalidation_rules[tool_name]:
            count = self.invalidate(invalidated_tool)
            total_invalidated += count
        
        return total_invalidated
    
    def add_invalidation_rule(
        self,
        trigger_tool: str,
        invalidated_tools: Set[str]
    ) -> None:
        """
        Add invalidation rule.
        
        When trigger_tool is executed, invalidate cached results for
        all tools in invalidated_tools.
        
        Args:
            trigger_tool: Tool that triggers invalidation
            invalidated_tools: Set of tools to invalidate
            
        Example:
            # When click is executed, invalidate screen_analyzer results
            cache.add_invalidation_rule('click', {'screen_analyzer'})
        """
        if trigger_tool not in self.invalidation_rules:
            self.invalidation_rules[trigger_tool] = set()
        
        self.invalidation_rules[trigger_tool].update(invalidated_tools)
        
        logger.debug(
            f"Added invalidation rule: {trigger_tool} -> {invalidated_tools}"
        )
    
    def clear(self) -> None:
        """Clear all cached entries."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache cleared ({count} entries removed)")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats['total_requests']
        hit_rate = (
            self.stats['hits'] / total_requests
            if total_requests > 0
            else 0.0
        )
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'evictions': self.stats['evictions'],
            'invalidations': self.stats['invalidations'],
            'total_requests': total_requests
        }


class CachedToolWrapper:
    """
    Wrapper that adds caching to any tool.
    
    Usage:
        cached_tool = CachedToolWrapper(original_tool, cache)
        result = cached_tool.execute(**kwargs)
    """
    
    def __init__(
        self,
        tool: Any,
        cache: ToolCache,
        cacheable: bool = True,
        invalidates: Optional[Set[str]] = None
    ):
        """
        Initialize cached tool wrapper.
        
        Args:
            tool: Original tool instance
            cache: ToolCache instance
            cacheable: Whether this tool's results should be cached
            invalidates: Set of tool names that this tool invalidates
        """
        self.tool = tool
        self.cache = cache
        self.cacheable = cacheable
        self.invalidates = invalidates or set()
        
        # Get tool metadata
        self.metadata = tool.get_metadata()
        self.tool_name = self.metadata.name
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute tool with caching.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        # Check cache if cacheable
        if self.cacheable:
            cached_result = self.cache.get(
                self.tool_name,
                args=(),
                kwargs=kwargs
            )
            
            if cached_result is not None:
                # Return cached result
                return cached_result
        
        # Execute tool
        result = self.tool.execute(**kwargs)
        
        # Cache result if successful and cacheable
        if self.cacheable and result.get('success', False):
            self.cache.put(
                self.tool_name,
                result,
                args=(),
                kwargs=kwargs
            )
        
        # Handle invalidations if this tool modifies state
        if self.invalidates:
            for invalidated_tool in self.invalidates:
                self.cache.invalidate(invalidated_tool)
        
        return result
    
    def get_metadata(self):
        """Forward metadata from wrapped tool."""
        return self.metadata


def create_default_cache() -> ToolCache:
    """
    Create a tool cache with sensible default invalidation rules.
    
    Returns:
        Configured ToolCache instance
    """
    cache = ToolCache(
        max_size=100,
        default_ttl=300.0,  # 5 minutes
        enable_stats=True
    )
    
    # Define invalidation rules for common tools
    # When GUI actions execute, invalidate screen analysis
    gui_actions = {'click', 'double_click', 'type_text', 'press_key', 'scroll'}
    for action in gui_actions:
        cache.add_invalidation_rule(action, {'screen_analyzer', 'analyze_screen'})
    
    # When files are written, invalidate file reads
    cache.add_invalidation_rule('file_write', {'file_read', 'file_list'})
    
    logger.info("Created default tool cache with invalidation rules")
    
    return cache
