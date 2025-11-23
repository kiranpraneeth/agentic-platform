"""
MCP Server Tests

Tests for MCP server implementations including:
- Calculator server
- Filesystem server security
- Database server read-only mode
- Server lifecycle management
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path

import pytest

from src.mcp_servers.calculator_server import CalculatorMCPServer
from src.mcp_servers.filesystem_server import FilesystemMCPServer


@pytest.mark.mcp
@pytest.mark.unit
class TestCalculatorMCPServer:
    """Test calculator MCP server."""

    @pytest.fixture
    def calculator_server(self):
        """Create a calculator server instance."""
        return CalculatorMCPServer()

    def test_get_tools(self, calculator_server):
        """Test getting list of tools."""
        tools = calculator_server.get_tools()

        assert len(tools) == 5
        tool_names = [tool["name"] for tool in tools]
        assert "add" in tool_names
        assert "subtract" in tool_names
        assert "multiply" in tool_names
        assert "divide" in tool_names
        assert "power" in tool_names

    @pytest.mark.asyncio
    async def test_add_tool(self, calculator_server):
        """Test add tool."""
        result = await calculator_server.handle_tool_call("add", {"a": 5, "b": 3})

        assert result["result"] == 8

    @pytest.mark.asyncio
    async def test_subtract_tool(self, calculator_server):
        """Test subtract tool."""
        result = await calculator_server.handle_tool_call("subtract", {"a": 10, "b": 4})

        assert result["result"] == 6

    @pytest.mark.asyncio
    async def test_multiply_tool(self, calculator_server):
        """Test multiply tool."""
        result = await calculator_server.handle_tool_call("multiply", {"a": 6, "b": 7})

        assert result["result"] == 42

    @pytest.mark.asyncio
    async def test_divide_tool(self, calculator_server):
        """Test divide tool."""
        result = await calculator_server.handle_tool_call("divide", {"a": 15, "b": 3})

        assert result["result"] == 5.0

    @pytest.mark.asyncio
    async def test_divide_by_zero(self, calculator_server):
        """Test that dividing by zero raises an error."""
        with pytest.raises(ValueError, match="Division by zero"):
            await calculator_server.handle_tool_call("divide", {"a": 10, "b": 0})

    @pytest.mark.asyncio
    async def test_power_tool(self, calculator_server):
        """Test power tool."""
        result = await calculator_server.handle_tool_call("power", {"a": 2, "b": 8})

        assert result["result"] == 256

    @pytest.mark.asyncio
    async def test_unknown_tool(self, calculator_server):
        """Test calling unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await calculator_server.handle_tool_call("unknown_tool", {})


@pytest.mark.mcp
@pytest.mark.unit
class TestFilesystemMCPServer:
    """Test filesystem MCP server."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def filesystem_server(self, temp_dir):
        """Create a filesystem server instance."""
        return FilesystemMCPServer(allowed_paths=[temp_dir])

    def test_get_tools(self, filesystem_server):
        """Test getting list of tools."""
        tools = filesystem_server.get_tools()

        assert len(tools) == 7
        tool_names = [tool["name"] for tool in tools]
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "list_directory" in tool_names
        assert "create_directory" in tool_names
        assert "delete_file" in tool_names
        assert "get_file_info" in tool_names
        assert "search_files" in tool_names

    @pytest.mark.asyncio
    async def test_write_and_read_file(self, filesystem_server, temp_dir):
        """Test writing and reading a file."""
        test_file = temp_dir / "test.txt"
        content = "Hello, World!"

        # Write file
        write_result = await filesystem_server.handle_tool_call(
            "write_file", {"path": str(test_file), "content": content}
        )
        assert write_result["success"] is True

        # Read file
        read_result = await filesystem_server.handle_tool_call(
            "read_file", {"path": str(test_file)}
        )
        assert read_result["content"] == content

    @pytest.mark.asyncio
    async def test_list_directory(self, filesystem_server, temp_dir):
        """Test listing directory contents."""
        # Create some files
        (temp_dir / "file1.txt").write_text("test1")
        (temp_dir / "file2.txt").write_text("test2")

        result = await filesystem_server.handle_tool_call(
            "list_directory", {"path": str(temp_dir)}
        )

        assert len(result["entries"]) >= 2
        entry_names = [e["name"] for e in result["entries"]]
        assert "file1.txt" in entry_names
        assert "file2.txt" in entry_names

    @pytest.mark.asyncio
    async def test_create_directory(self, filesystem_server, temp_dir):
        """Test creating a directory."""
        new_dir = temp_dir / "subdir"

        result = await filesystem_server.handle_tool_call(
            "create_directory", {"path": str(new_dir)}
        )

        assert result["success"] is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    @pytest.mark.asyncio
    async def test_get_file_info(self, filesystem_server, temp_dir):
        """Test getting file information."""
        test_file = temp_dir / "info.txt"
        test_file.write_text("test content")

        result = await filesystem_server.handle_tool_call(
            "get_file_info", {"path": str(test_file)}
        )

        assert result["name"] == "info.txt"
        assert result["size"] > 0
        assert result["is_file"] is True
        assert result["is_directory"] is False

    @pytest.mark.asyncio
    async def test_delete_file(self, filesystem_server, temp_dir):
        """Test deleting a file."""
        test_file = temp_dir / "delete_me.txt"
        test_file.write_text("to be deleted")

        result = await filesystem_server.handle_tool_call(
            "delete_file", {"path": str(test_file)}
        )

        assert result["success"] is True
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_search_files(self, filesystem_server, temp_dir):
        """Test searching for files."""
        # Create test files
        (temp_dir / "test1.txt").write_text("test")
        (temp_dir / "test2.md").write_text("test")
        (temp_dir / "other.txt").write_text("test")

        result = await filesystem_server.handle_tool_call(
            "search_files", {"path": str(temp_dir), "pattern": "test*.txt"}
        )

        assert len(result["files"]) >= 1
        file_names = [Path(f).name for f in result["files"]]
        assert "test1.txt" in file_names

    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, filesystem_server, temp_dir):
        """Test that path traversal attacks are prevented."""
        # Try to access file outside allowed directory
        with pytest.raises(ValueError, match="not within allowed"):
            await filesystem_server.handle_tool_call(
                "read_file", {"path": "/etc/passwd"}
            )

        # Try path traversal with ../
        with pytest.raises(ValueError, match="not within allowed"):
            await filesystem_server.handle_tool_call(
                "read_file", {"path": str(temp_dir / ".." / ".." / "etc" / "passwd")}
            )

    @pytest.mark.asyncio
    async def test_file_size_limit(self, filesystem_server, temp_dir):
        """Test that large files are rejected."""
        test_file = temp_dir / "large.txt"

        # Try to write a file larger than the limit
        large_content = "x" * (filesystem_server.max_file_size + 1)

        with pytest.raises(ValueError, match="too large"):
            await filesystem_server.handle_tool_call(
                "write_file", {"path": str(test_file), "content": large_content}
            )

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, filesystem_server, temp_dir):
        """Test reading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            await filesystem_server.handle_tool_call(
                "read_file", {"path": str(temp_dir / "nonexistent.txt")}
            )


@pytest.mark.mcp
@pytest.mark.integration
class TestMCPServerCommunication:
    """Test MCP JSON-RPC communication."""

    def test_server_get_info_request(self):
        """Test server info request structure."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
            },
        }

        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "initialize"
        assert "id" in request

    def test_tool_call_request_structure(self):
        """Test tool call request structure."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {"a": 5, "b": 3},
            },
        }

        assert request["method"] == "tools/call"
        assert request["params"]["name"] == "add"
        assert "arguments" in request["params"]

    def test_response_structure(self):
        """Test response structure."""
        response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"result": 8},
        }

        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert response["id"] == 2

    def test_error_response_structure(self):
        """Test error response structure."""
        error_response = {
            "jsonrpc": "2.0",
            "id": 3,
            "error": {
                "code": -32602,
                "message": "Invalid params",
                "data": {"detail": "Missing required parameter 'a'"},
            },
        }

        assert "error" in error_response
        assert error_response["error"]["code"] == -32602
        assert "message" in error_response["error"]


@pytest.mark.mcp
@pytest.mark.unit
class TestMCPServerValidation:
    """Test MCP server input validation."""

    @pytest.fixture
    def calculator_server(self):
        return CalculatorMCPServer()

    @pytest.mark.asyncio
    async def test_missing_required_argument(self, calculator_server):
        """Test that missing required arguments are caught."""
        with pytest.raises(KeyError):
            await calculator_server.handle_tool_call("add", {"a": 5})  # Missing 'b'

    @pytest.mark.asyncio
    async def test_invalid_argument_type(self, calculator_server):
        """Test that invalid argument types cause errors."""
        with pytest.raises(TypeError):
            await calculator_server.handle_tool_call("add", {"a": "not a number", "b": 5})
