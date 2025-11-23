#!/usr/bin/env python3
"""Filesystem MCP Server - Secure file system access for agents.

This server provides safe file system operations with:
- Path traversal prevention
- Sandboxing to allowed directories
- File size limits
- Type validation
"""

import os
import pathlib
from typing import Any

from src.mcp_servers.base_server import BaseMCPServer, run_server


class FilesystemMCPServer(BaseMCPServer):
    """MCP server for file system operations."""

    def __init__(self, allowed_paths: list[str] | None = None, max_file_size: int = 10 * 1024 * 1024):
        """Initialize filesystem server.

        Args:
            allowed_paths: List of allowed directory paths (defaults to /tmp)
            max_file_size: Maximum file size in bytes (default 10MB)
        """
        super().__init__(name="filesystem-server", version="1.0.0")
        self.allowed_paths = [pathlib.Path(p).resolve() for p in (allowed_paths or ["/tmp"])]
        self.max_file_size = max_file_size

    def _validate_path(self, file_path: str) -> pathlib.Path:
        """Validate and resolve file path.

        Args:
            file_path: Path to validate

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path is invalid or outside allowed directories
        """
        # Resolve to absolute path
        path = pathlib.Path(file_path).resolve()

        # Check if path is within allowed directories
        allowed = False
        for allowed_path in self.allowed_paths:
            try:
                path.relative_to(allowed_path)
                allowed = True
                break
            except ValueError:
                continue

        if not allowed:
            raise ValueError(
                f"Path {file_path} is not within allowed directories: "
                f"{[str(p) for p in self.allowed_paths]}"
            )

        return path

    def get_tools(self) -> list[dict[str, Any]]:
        """Return filesystem tool definitions."""
        return [
            {
                "name": "read_file",
                "description": "Read the contents of a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to read",
                        }
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": "Write content to a file (creates or overwrites)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to write",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
            {
                "name": "list_directory",
                "description": "List files and directories in a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the directory to list",
                        }
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "create_directory",
                "description": "Create a new directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the directory to create",
                        }
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "get_file_info",
                "description": "Get information about a file or directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to get information about",
                        }
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "delete_file",
                "description": "Delete a file (use with caution)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to delete",
                        }
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "search_files",
                "description": "Search for files by name pattern in a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to search in",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to match (e.g., '*.py', 'test_*.txt')",
                        },
                    },
                    "required": ["directory", "pattern"],
                },
            },
        ]

    async def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute filesystem tool."""
        handlers = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "list_directory": self._list_directory,
            "create_directory": self._create_directory,
            "get_file_info": self._get_file_info,
            "delete_file": self._delete_file,
            "search_files": self._search_files,
        }

        handler = handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        return await handler(arguments)

    async def _read_file(self, args: dict[str, Any]) -> dict[str, Any]:
        """Read file contents."""
        path = self._validate_path(args["path"])

        if not path.exists():
            raise ValueError(f"File not found: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Check file size
        size = path.stat().st_size
        if size > self.max_file_size:
            raise ValueError(f"File too large: {size} bytes (max {self.max_file_size})")

        # Read file
        content = path.read_text(encoding="utf-8")

        return {
            "path": str(path),
            "content": content,
            "size": size,
        }

    async def _write_file(self, args: dict[str, Any]) -> dict[str, Any]:
        """Write content to file."""
        path = self._validate_path(args["path"])
        content = args["content"]

        # Check content size
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > self.max_file_size:
            raise ValueError(f"Content too large: {len(content_bytes)} bytes (max {self.max_file_size})")

        # Create parent directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content, encoding="utf-8")

        return {
            "path": str(path),
            "size": len(content_bytes),
            "message": "File written successfully",
        }

    async def _list_directory(self, args: dict[str, Any]) -> dict[str, Any]:
        """List directory contents."""
        path = self._validate_path(args["path"])

        if not path.exists():
            raise ValueError(f"Directory not found: {path}")

        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        # List contents
        entries = []
        for entry in sorted(path.iterdir()):
            stat = entry.stat()
            entries.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "type": "directory" if entry.is_dir() else "file",
                    "size": stat.st_size if entry.is_file() else None,
                    "modified": stat.st_mtime,
                }
            )

        return {
            "path": str(path),
            "entries": entries,
            "count": len(entries),
        }

    async def _create_directory(self, args: dict[str, Any]) -> dict[str, Any]:
        """Create a directory."""
        path = self._validate_path(args["path"])

        if path.exists():
            raise ValueError(f"Path already exists: {path}")

        # Create directory
        path.mkdir(parents=True, exist_ok=False)

        return {
            "path": str(path),
            "message": "Directory created successfully",
        }

    async def _get_file_info(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get file/directory information."""
        path = self._validate_path(args["path"])

        if not path.exists():
            raise ValueError(f"Path not found: {path}")

        stat = path.stat()

        return {
            "path": str(path),
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
        }

    async def _delete_file(self, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a file."""
        path = self._validate_path(args["path"])

        if not path.exists():
            raise ValueError(f"File not found: {path}")

        if path.is_dir():
            raise ValueError(f"Cannot delete directory (use rmdir): {path}")

        # Delete file
        path.unlink()

        return {
            "path": str(path),
            "message": "File deleted successfully",
        }

    async def _search_files(self, args: dict[str, Any]) -> dict[str, Any]:
        """Search for files matching a pattern."""
        directory = self._validate_path(args["directory"])
        pattern = args["pattern"]

        if not directory.exists():
            raise ValueError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        # Search for files
        matches = []
        for match in directory.glob(pattern):
            # Ensure match is within allowed paths
            try:
                self._validate_path(str(match))
                stat = match.stat()
                matches.append(
                    {
                        "name": match.name,
                        "path": str(match),
                        "type": "directory" if match.is_dir() else "file",
                        "size": stat.st_size if match.is_file() else None,
                        "modified": stat.st_mtime,
                    }
                )
            except ValueError:
                # Skip files outside allowed paths
                continue

        return {
            "directory": str(directory),
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
        }


def main():
    """Main entry point."""
    import sys

    # Get allowed paths from command line args
    allowed_paths = sys.argv[1:] if len(sys.argv) > 1 else ["/tmp"]

    # Create and run server
    server = FilesystemMCPServer(allowed_paths=allowed_paths)
    run_server(server)


if __name__ == "__main__":
    main()
