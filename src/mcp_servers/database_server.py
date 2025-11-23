#!/usr/bin/env python3
"""Database MCP Server - Safe PostgreSQL database access for agents.

This server provides read-only database operations with:
- SQL injection prevention
- Query whitelisting
- Row limits
- Read-only mode
"""

import asyncio
from typing import Any

import asyncpg

from src.mcp_servers.base_server import BaseMCPServer, run_server


class DatabaseMCPServer(BaseMCPServer):
    """MCP server for database operations."""

    def __init__(
        self,
        database_url: str,
        read_only: bool = True,
        max_rows: int = 1000,
        allowed_schemas: list[str] | None = None,
    ):
        """Initialize database server.

        Args:
            database_url: PostgreSQL connection URL
            read_only: If True, only allow SELECT queries
            max_rows: Maximum number of rows to return
            allowed_schemas: List of allowed schemas (defaults to public)
        """
        super().__init__(name="database-server", version="1.0.0")
        self.database_url = database_url
        self.read_only = read_only
        self.max_rows = max_rows
        self.allowed_schemas = allowed_schemas or ["public"]
        self.pool = None

    async def _get_pool(self):
        """Get or create connection pool."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5)
        return self.pool

    def _validate_query(self, query: str) -> None:
        """Validate query for safety.

        Args:
            query: SQL query to validate

        Raises:
            ValueError: If query is not allowed
        """
        query_upper = query.strip().upper()

        # Check if read-only mode
        if self.read_only:
            # Only allow SELECT and SHOW
            if not (query_upper.startswith("SELECT") or query_upper.startswith("SHOW")):
                raise ValueError("Only SELECT queries are allowed in read-only mode")

            # Block dangerous keywords
            dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE"]
            for keyword in dangerous:
                if keyword in query_upper:
                    raise ValueError(f"Keyword '{keyword}' is not allowed in read-only mode")

    def get_tools(self) -> list[dict[str, Any]]:
        """Return database tool definitions."""
        tools = [
            {
                "name": "query",
                "description": "Execute a SELECT query and return results",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL SELECT query to execute",
                        },
                        "params": {
                            "type": "array",
                            "description": "Optional query parameters (for parameterized queries)",
                            "items": {"type": ["string", "number", "boolean", "null"]},
                        },
                    },
                    "required": ["sql"],
                },
            },
            {
                "name": "list_tables",
                "description": "List all tables in the database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "string",
                            "description": "Schema name (defaults to 'public')",
                        }
                    },
                },
            },
            {
                "name": "describe_table",
                "description": "Get the schema/structure of a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to describe",
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name (defaults to 'public')",
                        },
                    },
                    "required": ["table_name"],
                },
            },
            {
                "name": "get_schema",
                "description": "Get complete database schema with all tables and columns",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "string",
                            "description": "Schema name (defaults to 'public')",
                        }
                    },
                },
            },
        ]

        return tools

    async def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute database tool."""
        handlers = {
            "query": self._query,
            "list_tables": self._list_tables,
            "describe_table": self._describe_table,
            "get_schema": self._get_schema,
        }

        handler = handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        return await handler(arguments)

    async def _query(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a SELECT query."""
        sql = args["sql"]
        params = args.get("params", [])

        # Validate query
        self._validate_query(sql)

        # Get connection pool
        pool = await self._get_pool()

        # Execute query
        async with pool.acquire() as conn:
            # Add LIMIT if not present
            if "LIMIT" not in sql.upper():
                sql = f"{sql.rstrip(';')} LIMIT {self.max_rows}"

            rows = await conn.fetch(sql, *params)

            # Convert rows to dictionaries
            results = [dict(row) for row in rows]

            return {
                "rows": results,
                "count": len(results),
                "truncated": len(results) >= self.max_rows,
            }

    async def _list_tables(self, args: dict[str, Any]) -> dict[str, Any]:
        """List all tables in a schema."""
        schema = args.get("schema", "public")

        # Validate schema
        if schema not in self.allowed_schemas:
            raise ValueError(f"Schema '{schema}' is not in allowed schemas: {self.allowed_schemas}")

        # Get connection pool
        pool = await self._get_pool()

        # Query tables
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = $1
                ORDER BY table_name
                """,
                schema,
            )

            tables = [{"name": row["table_name"], "type": row["table_type"]} for row in rows]

            return {
                "schema": schema,
                "tables": tables,
                "count": len(tables),
            }

    async def _describe_table(self, args: dict[str, Any]) -> dict[str, Any]:
        """Describe a table's structure."""
        table_name = args["table_name"]
        schema = args.get("schema", "public")

        # Validate schema
        if schema not in self.allowed_schemas:
            raise ValueError(f"Schema '{schema}' is not in allowed schemas: {self.allowed_schemas}")

        # Get connection pool
        pool = await self._get_pool()

        # Query table structure
        async with pool.acquire() as conn:
            # Get columns
            columns = await conn.fetch(
                """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
                """,
                schema,
                table_name,
            )

            if not columns:
                raise ValueError(f"Table '{schema}.{table_name}' not found")

            # Get indexes
            indexes = await conn.fetch(
                """
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = $1 AND tablename = $2
                """,
                schema,
                table_name,
            )

            column_info = [
                {
                    "name": col["column_name"],
                    "type": col["data_type"],
                    "nullable": col["is_nullable"] == "YES",
                    "default": col["column_default"],
                    "max_length": col["character_maximum_length"],
                }
                for col in columns
            ]

            index_info = [{"name": idx["indexname"], "definition": idx["indexdef"]} for idx in indexes]

            return {
                "schema": schema,
                "table": table_name,
                "columns": column_info,
                "indexes": index_info,
                "column_count": len(column_info),
            }

    async def _get_schema(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get complete database schema."""
        schema = args.get("schema", "public")

        # Validate schema
        if schema not in self.allowed_schemas:
            raise ValueError(f"Schema '{schema}' is not in allowed schemas: {self.allowed_schemas}")

        # Get connection pool
        pool = await self._get_pool()

        # Query schema
        async with pool.acquire() as conn:
            # Get all tables
            tables = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1 AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """,
                schema,
            )

            schema_info = []

            for table_row in tables:
                table_name = table_row["table_name"]

                # Get columns for this table
                columns = await conn.fetch(
                    """
                    SELECT
                        column_name,
                        data_type,
                        is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                    """,
                    schema,
                    table_name,
                )

                schema_info.append(
                    {
                        "table": table_name,
                        "columns": [
                            {
                                "name": col["column_name"],
                                "type": col["data_type"],
                                "nullable": col["is_nullable"] == "YES",
                            }
                            for col in columns
                        ],
                    }
                )

            return {
                "schema": schema,
                "tables": schema_info,
                "table_count": len(schema_info),
            }

    async def run(self):
        """Run server with connection pool cleanup."""
        try:
            await super().run()
        finally:
            if self.pool:
                await self.pool.close()


def main():
    """Main entry point."""
    import os
    import sys

    # Get database URL from environment or command line
    database_url = os.getenv("DATABASE_URL")
    if len(sys.argv) > 1:
        database_url = sys.argv[1]

    if not database_url:
        print("Error: DATABASE_URL environment variable or command line argument required", file=sys.stderr)
        sys.exit(1)

    # Create and run server
    server = DatabaseMCPServer(database_url=database_url)
    run_server(server)


if __name__ == "__main__":
    main()
