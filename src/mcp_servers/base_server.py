"""Base MCP Server implementation with JSON-RPC protocol handling."""

import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """Base class for MCP servers implementing the JSON-RPC protocol.

    Subclasses should:
    1. Call super().__init__() in their __init__
    2. Implement get_tools() to return tool definitions
    3. Implement handle_tool_call() to execute tools
    4. Optionally implement get_resources() for resource support
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.initialized = False
        self.client_info = None

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """Return list of tool definitions.

        Each tool should have:
        - name: str
        - description: str
        - inputSchema: dict (JSON Schema)
        """
        pass

    @abstractmethod
    async def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from the client

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool is not found or arguments are invalid
        """
        pass

    def get_resources(self) -> list[dict[str, Any]]:
        """Return list of resource definitions (optional).

        Each resource should have:
        - uri: str
        - name: str
        - description: str (optional)
        - mimeType: str (optional)
        """
        return []

    def get_prompts(self) -> list[dict[str, Any]]:
        """Return list of prompt templates (optional)."""
        return []

    async def handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialize request."""
        self.client_info = params.get("clientInfo")
        self.initialized = True

        return {
            "protocolVersion": "1.0",
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
            },
        }

    async def handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/list request."""
        return {"tools": self.get_tools()}

    async def handle_resources_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle resources/list request."""
        return {"resources": self.get_resources()}

    async def handle_prompts_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle prompts/list request."""
        return {"prompts": self.get_prompts()}

    async def handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Tool name is required")

        # Execute the tool
        result = await self.handle_tool_call(tool_name, arguments)

        return {"content": result}

    async def handle_ping(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle ping request."""
        return {}

    async def handle_request(self, method: str, params: dict[str, Any]) -> Any:
        """Route request to appropriate handler."""
        handlers = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_tools_list,
            "tools/call": self.handle_tools_call,
            "resources/list": self.handle_resources_list,
            "prompts/list": self.handle_prompts_list,
            "ping": self.handle_ping,
        }

        handler = handlers.get(method)
        if not handler:
            raise ValueError(f"Unknown method: {method}")

        return await handler(params)

    async def send_response(self, request_id: int | str, result: Any = None, error: dict | None = None):
        """Send JSON-RPC response to stdout."""
        response = {"jsonrpc": "2.0", "id": request_id}

        if error:
            response["error"] = error
        else:
            response["result"] = result

        # Write to stdout
        output = json.dumps(response) + "\n"
        sys.stdout.write(output)
        sys.stdout.flush()

    async def run(self):
        """Main server loop - read from stdin, process requests, write to stdout."""
        logger.info(f"Starting MCP server: {self.name} v{self.version}")

        try:
            # Read from stdin line by line
            while True:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

                if not line:
                    # EOF reached
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON-RPC request
                    request = json.loads(line)
                    request_id = request.get("id")
                    method = request.get("method")
                    params = request.get("params", {})

                    logger.debug(f"Received request: {method}")

                    # Handle request
                    result = await self.handle_request(method, params)

                    # Send response
                    await self.send_response(request_id, result=result)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    await self.send_response(
                        None,
                        error={"code": -32700, "message": "Parse error", "data": str(e)},
                    )

                except ValueError as e:
                    logger.error(f"Invalid request: {e}")
                    await self.send_response(
                        request.get("id"),
                        error={"code": -32602, "message": "Invalid params", "data": str(e)},
                    )

                except Exception as e:
                    logger.error(f"Internal error: {e}", exc_info=True)
                    await self.send_response(
                        request.get("id"),
                        error={"code": -32603, "message": "Internal error", "data": str(e)},
                    )

        except KeyboardInterrupt:
            logger.info("Server interrupted")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
        finally:
            logger.info("Server stopped")


def run_server(server: BaseMCPServer):
    """Run an MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],  # Log to stderr, not stdout
    )

    # Run the server
    asyncio.run(server.run())
