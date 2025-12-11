"""File operation tools for handling unstructured data."""

import os
from pathlib import Path
from typing import Any, Dict, List
from loguru import logger

from digital_humain.tools.base import BaseTool, ToolMetadata, ToolParameter


class FileReadTool(BaseTool):
    """Tool for reading file contents."""
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="file_read",
            description="Read contents of a file",
            parameters=[
                ToolParameter(
                    name="path",
                    type="str",
                    description="Path to file to read",
                    required=True
                )
            ],
            returns="str"
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute file read."""
        path = kwargs.get("path")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Read file: {path} ({len(content)} chars)")
            return {
                "success": True,
                "result": content,
                "metadata": {
                    "path": path,
                    "size": len(content)
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class FileWriteTool(BaseTool):
    """Tool for writing file contents."""
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="file_write",
            description="Write contents to a file",
            parameters=[
                ToolParameter(
                    name="path",
                    type="str",
                    description="Path to file to write",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type="str",
                    description="Content to write",
                    required=True
                ),
                ToolParameter(
                    name="mode",
                    type="str",
                    description="Write mode ('w' for overwrite, 'a' for append)",
                    required=False,
                    default="w"
                )
            ],
            returns="bool"
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute file write."""
        path = kwargs.get("path")
        content = kwargs.get("content")
        mode = kwargs.get("mode", "w")
        
        try:
            # Create parent directories if needed
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Wrote file: {path} ({len(content)} chars, mode={mode})")
            return {
                "success": True,
                "result": True,
                "metadata": {
                    "path": path,
                    "size": len(content),
                    "mode": mode
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class FileListTool(BaseTool):
    """Tool for listing files in a directory."""
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="file_list",
            description="List files in a directory",
            parameters=[
                ToolParameter(
                    name="path",
                    type="str",
                    description="Directory path to list",
                    required=True
                ),
                ToolParameter(
                    name="pattern",
                    type="str",
                    description="Optional glob pattern to filter files",
                    required=False,
                    default="*"
                )
            ],
            returns="List[str]"
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute file list."""
        path = kwargs.get("path")
        pattern = kwargs.get("pattern", "*")
        
        try:
            dir_path = Path(path)
            
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {path}"
                }
            
            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"Not a directory: {path}"
                }
            
            # List files matching pattern
            files = [str(f) for f in dir_path.glob(pattern) if f.is_file()]
            
            logger.info(f"Listed {len(files)} files in {path}")
            return {
                "success": True,
                "result": files,
                "metadata": {
                    "path": path,
                    "pattern": pattern,
                    "count": len(files)
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to list files in {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
