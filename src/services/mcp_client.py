"""MCP (Model Context Protocol) Client Service.

This service manages connections to MCP servers and handles tool execution.
"""

import asyncio
import json
import logging
import subprocess
import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import MCPServer, MCPServerConfig, MCPToolExecution

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Base exception for MCP client errors."""

    pass


class MCPServerConnectionError(MCPClientError):
    """Raised when connection to MCP server fails."""

    pass


class MCPToolExecutionError(MCPClientError):
    """Raised when tool execution fails."""

    pass


class MCPServerProcess:
    """Manages a single MCP server process with stdio communication."""

    def __init__(
        self,
        server_id: uuid.UUID,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ):
        self.server_id = server_id
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.timeout = timeout
        self.process: asyncio.subprocess.Process | None = None
        self.request_id = 0
        self.pending_requests: dict[int, asyncio.Future] = {}
        self._reader_task: asyncio.Task | None = None
        self._tools: list[dict[str, Any]] = []
        self._resources: list[dict[str, Any]] = []

    async def start(self) -> None:
        """Start the MCP server process."""
        try:
            # Build command with args
            cmd = [self.command] + self.args

            logger.info(f"Starting MCP server {self.server_id}: {' '.join(cmd)}")

            # Start process with stdio pipes
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env,
            )

            # Start reading responses
            self._reader_task = asyncio.create_task(self._read_responses())

            # Initialize connection and discover tools
            await self._initialize()

            logger.info(f"MCP server {self.server_id} started successfully")

        except Exception as e:
            logger.error(f"Failed to start MCP server {self.server_id}: {e}")
            await self.stop()
            raise MCPServerConnectionError(f"Failed to start server: {e}")

    async def stop(self) -> None:
        """Stop the MCP server process."""
        try:
            if self._reader_task:
                self._reader_task.cancel()
                try:
                    await self._reader_task
                except asyncio.CancelledError:
                    pass

            if self.process:
                try:
                    self.process.terminate()
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()

            self.process = None
            self.pending_requests.clear()

            logger.info(f"MCP server {self.server_id} stopped")

        except Exception as e:
            logger.error(f"Error stopping MCP server {self.server_id}: {e}")

    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Send JSON-RPC request to MCP server."""
        if not self.process or not self.process.stdin:
            raise MCPServerConnectionError("Server process not running")

        self.request_id += 1
        request_id = self.request_id

        request = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self.pending_requests[request_id] = future

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            # Wait for response with timeout
            result = await asyncio.wait_for(future, timeout=self.timeout)
            return result

        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise MCPToolExecutionError(f"Request timeout after {self.timeout}s")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise MCPToolExecutionError(f"Request failed: {e}")

    async def _read_responses(self) -> None:
        """Read and process responses from MCP server."""
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break

                try:
                    response = json.loads(line.decode().strip())

                    # Handle JSON-RPC response
                    if "id" in response:
                        request_id = response["id"]
                        future = self.pending_requests.pop(request_id, None)
                        if future and not future.done():
                            if "error" in response:
                                error = response["error"]
                                future.set_exception(
                                    MCPToolExecutionError(
                                        f"{error.get('message', 'Unknown error')} (code: {error.get('code')})"
                                    )
                                )
                            else:
                                future.set_result(response.get("result"))

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from MCP server: {e}")
                except Exception as e:
                    logger.error(f"Error processing response: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading responses: {e}")

    async def _initialize(self) -> None:
        """Initialize connection and discover tools."""
        try:
            # Send initialize request
            result = await self._send_request(
                "initialize",
                {
                    "protocolVersion": "1.0",
                    "capabilities": {"tools": {}, "resources": {}},
                    "clientInfo": {"name": "agentic-platform", "version": "1.0.0"},
                },
            )

            logger.info(f"MCP server initialized: {result}")

            # Discover tools
            tools_result = await self._send_request("tools/list", {})
            self._tools = tools_result.get("tools", [])
            logger.info(f"Discovered {len(self._tools)} tools")

            # Discover resources
            try:
                resources_result = await self._send_request("resources/list", {})
                self._resources = resources_result.get("resources", [])
                logger.info(f"Discovered {len(self._resources)} resources")
            except Exception as e:
                logger.warning(f"Failed to discover resources: {e}")

        except Exception as e:
            raise MCPServerConnectionError(f"Failed to initialize: {e}")

    async def execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool on the MCP server."""
        try:
            result = await self._send_request(
                "tools/call", {"name": tool_name, "arguments": tool_input}
            )

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise MCPToolExecutionError(f"Failed to execute tool {tool_name}: {e}")

    def get_tools(self) -> list[dict[str, Any]]:
        """Get list of available tools."""
        return self._tools

    def get_resources(self) -> list[dict[str, Any]]:
        """Get list of available resources."""
        return self._resources

    async def health_check(self) -> bool:
        """Check if server is healthy."""
        try:
            if not self.process or self.process.returncode is not None:
                return False

            # Send ping request
            await self._send_request("ping", {})
            return True

        except Exception:
            return False


class MCPClient:
    """MCP Client for managing multiple MCP servers and executing tools."""

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.servers: dict[uuid.UUID, MCPServerProcess] = {}

    async def connect_server(self, server_id: uuid.UUID) -> MCPServerProcess:
        """Connect to an MCP server."""
        # Check if already connected
        if server_id in self.servers:
            process = self.servers[server_id]
            if await process.health_check():
                return process
            else:
                # Server is unhealthy, reconnect
                await process.stop()
                del self.servers[server_id]

        # Get server configuration from database
        result = await self.db.execute(
            select(MCPServer).where(
                MCPServer.id == server_id,
                MCPServer.tenant_id == self.tenant_id,
                MCPServer.deleted_at.is_(None),
            )
        )
        server = result.scalar_one_or_none()

        if not server:
            raise MCPServerConnectionError(f"Server {server_id} not found")

        if server.status not in ["active", "ready", "running"]:
            raise MCPServerConnectionError(f"Server {server_id} is not active (status: {server.status})")

        if not server.command:
            raise MCPServerConnectionError(f"Server {server_id} has no command configured")

        # Get server config for this tenant (if exists)
        config_result = await self.db.execute(
            select(MCPServerConfig).where(
                MCPServerConfig.server_id == server_id,
                MCPServerConfig.tenant_id == self.tenant_id,
                MCPServerConfig.enabled == True,  # noqa: E712
            )
        )
        config = config_result.scalar_one_or_none()

        # Build environment variables
        env = dict(server.env_vars) if server.env_vars else {}
        if config and config.env_overrides:
            env.update(config.env_overrides)

        # Get timeout
        timeout = config.timeout_seconds if config else 30

        # Create and start server process
        process = MCPServerProcess(
            server_id=server_id, command=server.command, args=server.args, env=env, timeout=timeout
        )

        await process.start()

        # Update server status
        server.status = "running"
        server.last_health_check = datetime.utcnow()
        server.health_status = "healthy"
        await self.db.commit()

        self.servers[server_id] = process
        return process

    async def disconnect_server(self, server_id: uuid.UUID) -> None:
        """Disconnect from an MCP server."""
        if server_id in self.servers:
            process = self.servers[server_id]
            await process.stop()
            del self.servers[server_id]

            # Update server status
            result = await self.db.execute(
                select(MCPServer).where(MCPServer.id == server_id, MCPServer.tenant_id == self.tenant_id)
            )
            server = result.scalar_one_or_none()
            if server:
                server.status = "stopped"
                await self.db.commit()

    async def execute_tool(
        self,
        server_id: uuid.UUID,
        tool_name: str,
        tool_input: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
        message_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Execute a tool on an MCP server."""
        start_time = time.time()
        execution_id = uuid.uuid4()

        # Create execution log
        execution = MCPToolExecution(
            id=execution_id,
            tenant_id=self.tenant_id,
            server_id=server_id,
            conversation_id=conversation_id,
            message_id=message_id,
            agent_id=agent_id,
            tool_name=tool_name,
            tool_input=tool_input,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(execution)
        await self.db.commit()

        try:
            # Connect to server if not already connected
            process = await self.connect_server(server_id)

            # Check if tool is allowed
            config_result = await self.db.execute(
                select(MCPServerConfig).where(
                    MCPServerConfig.server_id == server_id,
                    MCPServerConfig.tenant_id == self.tenant_id,
                    MCPServerConfig.enabled == True,  # noqa: E712
                )
            )
            config = config_result.scalar_one_or_none()

            if config:
                # Check denied tools
                if config.denied_tools and tool_name in config.denied_tools:
                    raise MCPToolExecutionError(f"Tool {tool_name} is denied")

                # Check allowed tools
                if config.allowed_tools and tool_name not in config.allowed_tools:
                    raise MCPToolExecutionError(f"Tool {tool_name} is not in allowed list")

            # Execute tool
            tool_output = await process.execute_tool(tool_name, tool_input)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Update execution log
            execution.status = "success"
            execution.tool_output = tool_output
            execution.execution_time_ms = execution_time_ms
            execution.completed_at = datetime.utcnow()

            # Update server statistics
            result = await self.db.execute(
                select(MCPServer).where(MCPServer.id == server_id, MCPServer.tenant_id == self.tenant_id)
            )
            server = result.scalar_one_or_none()
            if server:
                server.total_executions += 1
                server.successful_executions += 1

            await self.db.commit()

            return {
                "execution_id": execution_id,
                "status": "success",
                "output": tool_output,
                "execution_time_ms": execution_time_ms,
            }

        except Exception as e:
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Update execution log
            execution.status = "error"
            execution.error_message = str(e)
            execution.execution_time_ms = execution_time_ms
            execution.completed_at = datetime.utcnow()

            # Update server statistics
            result = await self.db.execute(
                select(MCPServer).where(MCPServer.id == server_id, MCPServer.tenant_id == self.tenant_id)
            )
            server = result.scalar_one_or_none()
            if server:
                server.total_executions += 1
                server.failed_executions += 1

            await self.db.commit()

            raise

    async def discover_tools(self, server_id: uuid.UUID) -> list[dict[str, Any]]:
        """Discover available tools from an MCP server."""
        process = await self.connect_server(server_id)
        return process.get_tools()

    async def discover_resources(self, server_id: uuid.UUID) -> list[dict[str, Any]]:
        """Discover available resources from an MCP server."""
        process = await self.connect_server(server_id)
        return process.get_resources()

    async def health_check_server(self, server_id: uuid.UUID) -> bool:
        """Check health of an MCP server."""
        if server_id in self.servers:
            return await self.servers[server_id].health_check()
        return False

    async def close_all(self) -> None:
        """Close all server connections."""
        for server_id in list(self.servers.keys()):
            await self.disconnect_server(server_id)
