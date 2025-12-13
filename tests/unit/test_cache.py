"""Unit tests for tool caching."""

import pytest
import time
from digital_humain.tools.cache import (
    CacheEntry,
    ToolCache,
    CachedToolWrapper,
    create_default_cache
)


class TestCacheEntry:
    """Test CacheEntry functionality."""
    
    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test_key",
            result={"success": True, "data": "test"},
            tool_name="test_tool",
            timestamp=time.time()
        )
        
        assert entry.key == "test_key"
        assert entry.result["success"] is True
        assert entry.tool_name == "test_tool"
        assert entry.access_count == 0
    
    def test_cache_entry_access(self):
        """Test recording cache accesses."""
        entry = CacheEntry("key", "result", "tool", time.time())
        
        assert entry.access_count == 0
        
        entry.access()
        assert entry.access_count == 1
        
        entry.access()
        assert entry.access_count == 2
    
    def test_cache_entry_age(self):
        """Test cache entry age calculation."""
        past_time = time.time() - 10  # 10 seconds ago
        entry = CacheEntry("key", "result", "tool", past_time)
        
        age = entry.age()
        assert age >= 10  # Should be at least 10 seconds old


class TestToolCache:
    """Test ToolCache functionality."""
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = ToolCache(max_size=50, default_ttl=60.0)
        
        assert cache.max_size == 50
        assert cache.default_ttl == 60.0
        assert len(cache.cache) == 0
    
    def test_cache_put_and_get(self):
        """Test storing and retrieving from cache."""
        cache = ToolCache(max_size=10)
        
        # Put item
        cache.put(
            tool_name="test_tool",
            result={"success": True, "value": 42},
            args=(),
            kwargs={"param": "test"}
        )
        
        # Get item
        result = cache.get(
            tool_name="test_tool",
            args=(),
            kwargs={"param": "test"}
        )
        
        assert result is not None
        assert result["success"] is True
        assert result["value"] == 42
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = ToolCache()
        
        result = cache.get(
            tool_name="nonexistent",
            args=(),
            kwargs={}
        )
        
        assert result is None
        assert cache.stats['misses'] == 1
    
    def test_cache_hit_statistics(self):
        """Test cache hit statistics."""
        cache = ToolCache()
        
        # Store item
        cache.put("tool", "result", args=(1,))
        
        # Get item (hit)
        cache.get("tool", args=(1,))
        
        assert cache.stats['hits'] == 1
        assert cache.stats['total_requests'] == 1
        
        # Get different item (miss)
        cache.get("tool", args=(2,))
        
        assert cache.stats['misses'] == 1
        assert cache.stats['total_requests'] == 2
    
    def test_cache_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = ToolCache(default_ttl=0.1)  # 100ms TTL
        
        # Store item
        cache.put("tool", "result", kwargs={"key": "value"})
        
        # Immediate get should succeed
        result = cache.get("tool", kwargs={"key": "value"})
        assert result == "result"
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should be expired now
        result = cache.get("tool", kwargs={"key": "value"})
        assert result is None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = ToolCache(max_size=3)
        
        # Fill cache
        cache.put("tool1", "result1")
        cache.put("tool2", "result2")
        cache.put("tool3", "result3")
        
        # Access tool1 (make it more recent)
        cache.get("tool1")
        
        # Add new item (should evict tool2, the least recently used)
        cache.put("tool4", "result4")
        
        assert cache.stats['evictions'] == 1
        assert cache.get("tool1") is not None  # Still in cache
        assert cache.get("tool2") is None  # Evicted
        assert cache.get("tool3") is not None  # Still in cache
        assert cache.get("tool4") is not None  # Newly added
    
    def test_cache_invalidate(self):
        """Test cache invalidation."""
        cache = ToolCache()
        
        # Store multiple entries for same tool
        cache.put("screen_analyzer", "result1", args=(1,))
        cache.put("screen_analyzer", "result2", args=(2,))
        cache.put("other_tool", "result3", args=(3,))
        
        # Invalidate screen_analyzer
        count = cache.invalidate("screen_analyzer")
        
        assert count == 2
        assert cache.get("screen_analyzer", args=(1,)) is None
        assert cache.get("screen_analyzer", args=(2,)) is None
        assert cache.get("other_tool", args=(3,)) is not None
    
    def test_cache_invalidation_rules(self):
        """Test invalidation rules."""
        cache = ToolCache()
        
        # Add invalidation rule: clicking invalidates screen analysis
        cache.add_invalidation_rule("click", {"screen_analyzer", "analyze_screen"})
        
        # Store cached results
        cache.put("screen_analyzer", "result1")
        cache.put("analyze_screen", "result2")
        cache.put("unrelated_tool", "result3")
        
        # Trigger invalidation by clicking
        count = cache.invalidate_by_rules("click")
        
        assert count == 2
        assert cache.get("screen_analyzer") is None
        assert cache.get("analyze_screen") is None
        assert cache.get("unrelated_tool") is not None
    
    def test_cache_clear(self):
        """Test clearing the cache."""
        cache = ToolCache()
        
        # Add items
        cache.put("tool1", "result1")
        cache.put("tool2", "result2")
        
        assert len(cache.cache) == 2
        
        # Clear cache
        cache.clear()
        
        assert len(cache.cache) == 0
    
    def test_cache_statistics(self):
        """Test cache statistics."""
        cache = ToolCache()
        
        # Perform operations
        cache.put("tool", "result")
        cache.get("tool")  # Hit
        cache.get("missing")  # Miss
        
        stats = cache.get_stats()
        
        assert stats['size'] == 1
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5
        assert stats['total_requests'] == 2


class TestCachedToolWrapper:
    """Test CachedToolWrapper functionality."""
    
    def test_wrapper_initialization(self):
        """Test wrapper initialization."""
        from digital_humain.tools.file_tools import FileReadTool
        
        tool = FileReadTool()
        cache = ToolCache()
        wrapper = CachedToolWrapper(tool, cache, cacheable=True)
        
        assert wrapper.tool == tool
        assert wrapper.cache == cache
        assert wrapper.cacheable is True
    
    def test_wrapper_caches_results(self):
        """Test that wrapper caches successful results."""
        # Create mock tool
        class MockTool:
            def __init__(self):
                self.call_count = 0
            
            def get_metadata(self):
                from digital_humain.tools.base import ToolMetadata
                return ToolMetadata(name="mock_tool", description="Mock")
            
            def execute(self, **kwargs):
                self.call_count += 1
                return {"success": True, "result": f"call_{self.call_count}"}
        
        tool = MockTool()
        cache = ToolCache()
        wrapper = CachedToolWrapper(tool, cache, cacheable=True)
        
        # First call - should execute
        result1 = wrapper.execute(param="test")
        assert result1["result"] == "call_1"
        assert tool.call_count == 1
        
        # Second call with same params - should use cache
        result2 = wrapper.execute(param="test")
        assert result2["result"] == "call_1"  # Same result
        assert tool.call_count == 1  # Not called again
        
        # Different params - should execute again
        result3 = wrapper.execute(param="different")
        assert result3["result"] == "call_2"
        assert tool.call_count == 2
    
    def test_wrapper_handles_failures(self):
        """Test that wrapper doesn't cache failures."""
        class FailingTool:
            def __init__(self):
                self.call_count = 0
            
            def get_metadata(self):
                from digital_humain.tools.base import ToolMetadata
                return ToolMetadata(name="failing_tool", description="Fails")
            
            def execute(self, **kwargs):
                self.call_count += 1
                return {"success": False, "error": "Failed"}
        
        tool = FailingTool()
        cache = ToolCache()
        wrapper = CachedToolWrapper(tool, cache, cacheable=True)
        
        # First call - failure
        result1 = wrapper.execute()
        assert result1["success"] is False
        
        # Second call - should not use cache, execute again
        result2 = wrapper.execute()
        assert tool.call_count == 2  # Called twice
    
    def test_wrapper_invalidates_others(self):
        """Test that wrapper invalidates other tools."""
        class StatefulTool:
            def get_metadata(self):
                from digital_humain.tools.base import ToolMetadata
                return ToolMetadata(name="click", description="Click")
            
            def execute(self, **kwargs):
                return {"success": True}
        
        tool = StatefulTool()
        cache = ToolCache()
        
        # Pre-populate cache
        cache.put("screen_analyzer", "cached_result")
        
        # Create wrapper that invalidates screen_analyzer
        wrapper = CachedToolWrapper(
            tool,
            cache,
            invalidates={"screen_analyzer"}
        )
        
        # Execute (should invalidate screen_analyzer)
        wrapper.execute()
        
        # Check that screen_analyzer was invalidated
        assert cache.get("screen_analyzer") is None


class TestCreateDefaultCache:
    """Test create_default_cache function."""
    
    def test_default_cache_creation(self):
        """Test creating default cache with rules."""
        cache = create_default_cache()
        
        assert cache.max_size == 100
        assert cache.default_ttl == 300.0
        
        # Check that invalidation rules were added
        assert "click" in cache.invalidation_rules
        assert "screen_analyzer" in cache.invalidation_rules["click"]
        assert "file_write" in cache.invalidation_rules
    
    def test_default_invalidation_rules(self):
        """Test default invalidation rules work correctly."""
        cache = create_default_cache()
        
        # Add cached screen analysis
        cache.put("screen_analyzer", "result")
        
        # Trigger click invalidation
        count = cache.invalidate_by_rules("click")
        
        assert count >= 1  # Should invalidate screen_analyzer
