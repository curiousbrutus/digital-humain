"""Unit tests for tool system."""

import pytest
from pathlib import Path
import tempfile
import os

from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.file_tools import FileReadTool, FileWriteTool, FileListTool


class TestToolRegistry:
    """Test ToolRegistry functionality."""
    
    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        tool = FileReadTool()
        
        registry.register(tool)
        
        assert "file_read" in registry.list_tools()
        assert registry.get("file_read") is not None
    
    def test_unregister_tool(self):
        """Test tool unregistration."""
        registry = ToolRegistry()
        tool = FileReadTool()
        
        registry.register(tool)
        assert registry.unregister("file_read") is True
        assert "file_read" not in registry.list_tools()
    
    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None


class TestFileTools:
    """Test file operation tools."""
    
    def test_file_read_tool(self):
        """Test FileReadTool."""
        tool = FileReadTool()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            result = tool.execute(path=temp_path)
            assert result["success"] is True
            assert result["result"] == "test content"
        finally:
            os.unlink(temp_path)
    
    def test_file_write_tool(self):
        """Test FileWriteTool."""
        tool = FileWriteTool()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "test.txt")
            
            result = tool.execute(path=temp_path, content="hello world")
            assert result["success"] is True
            
            # Verify content
            with open(temp_path, 'r') as f:
                assert f.read() == "hello world"
    
    def test_file_list_tool(self):
        """Test FileListTool."""
        tool = FileListTool()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "file1.txt").touch()
            Path(tmpdir, "file2.txt").touch()
            Path(tmpdir, "file3.py").touch()
            
            result = tool.execute(path=tmpdir, pattern="*.txt")
            assert result["success"] is True
            assert len(result["result"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
