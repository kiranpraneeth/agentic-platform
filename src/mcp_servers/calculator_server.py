#!/usr/bin/env python3
"""Calculator MCP Server - Simple math operations for testing.

This is a simple MCP server for testing and demonstration purposes.
It provides basic calculator operations.
"""

from typing import Any

from src.mcp_servers.base_server import BaseMCPServer, run_server


class CalculatorMCPServer(BaseMCPServer):
    """MCP server for calculator operations."""

    def __init__(self):
        """Initialize calculator server."""
        super().__init__(name="calculator-server", version="1.0.0")

    def get_tools(self) -> list[dict[str, Any]]:
        """Return calculator tool definitions."""
        return [
            {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "subtract",
                "description": "Subtract two numbers (a - b)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "Number to subtract from"},
                        "b": {"type": "number", "description": "Number to subtract"},
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "multiply",
                "description": "Multiply two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "divide",
                "description": "Divide two numbers (a / b)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "Dividend"},
                        "b": {"type": "number", "description": "Divisor"},
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "power",
                "description": "Raise a number to a power (a ^ b)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base": {"type": "number", "description": "Base number"},
                        "exponent": {"type": "number", "description": "Exponent"},
                    },
                    "required": ["base", "exponent"],
                },
            },
        ]

    async def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute calculator tool."""
        if tool_name == "add":
            return {"result": arguments["a"] + arguments["b"]}

        elif tool_name == "subtract":
            return {"result": arguments["a"] - arguments["b"]}

        elif tool_name == "multiply":
            return {"result": arguments["a"] * arguments["b"]}

        elif tool_name == "divide":
            if arguments["b"] == 0:
                raise ValueError("Division by zero")
            return {"result": arguments["a"] / arguments["b"]}

        elif tool_name == "power":
            return {"result": arguments["base"] ** arguments["exponent"]}

        else:
            raise ValueError(f"Unknown tool: {tool_name}")


def main():
    """Main entry point."""
    server = CalculatorMCPServer()
    run_server(server)


if __name__ == "__main__":
    main()
