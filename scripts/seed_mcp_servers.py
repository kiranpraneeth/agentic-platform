"""Seed MCP servers into the database."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.core.config import settings
from src.db.models import MCPServer, Tenant
from src.db.session import AsyncSessionLocal


async def seed_mcp_servers():
    """Seed MCP servers for development."""
    async with AsyncSessionLocal() as db:
        # Get demo tenant
        result = await db.execute(select(Tenant).where(Tenant.slug == "demo-tenant"))
        tenant = result.scalar_one_or_none()

        if not tenant:
            print("Error: Demo tenant not found. Run seed_dev_data.py first.")
            return

        print(f"Seeding MCP servers for tenant: {tenant.name}")

        # Define MCP servers
        servers = [
            {
                "name": "Filesystem Server",
                "slug": "filesystem",
                "description": "Safe file system access with sandboxing and path validation",
                "server_type": "stdio",
                "command": "python",
                "args": [
                    "-m",
                    "src.mcp_servers.filesystem_server",
                    "/tmp",  # Allowed path
                ],
                "category": "system",
                "author": "Platform Team",
                "status": "inactive",
                "visibility": "private",
                "tools": [
                    {"name": "read_file", "description": "Read file contents"},
                    {"name": "write_file", "description": "Write content to file"},
                    {"name": "list_directory", "description": "List directory contents"},
                    {"name": "create_directory", "description": "Create new directory"},
                    {"name": "get_file_info", "description": "Get file/directory info"},
                    {"name": "delete_file", "description": "Delete a file"},
                    {"name": "search_files", "description": "Search files by pattern"},
                ],
                "config": {
                    "max_file_size": 10 * 1024 * 1024,  # 10MB
                    "allowed_paths": ["/tmp"],
                },
            },
            {
                "name": "Database Server",
                "slug": "database",
                "description": "Read-only PostgreSQL database access with query validation",
                "server_type": "stdio",
                "command": "python",
                "args": ["-m", "src.mcp_servers.database_server"],
                "category": "data",
                "author": "Platform Team",
                "status": "inactive",
                "visibility": "private",
                "tools": [
                    {"name": "query", "description": "Execute SELECT query"},
                    {"name": "list_tables", "description": "List all tables"},
                    {"name": "describe_table", "description": "Get table structure"},
                    {"name": "get_schema", "description": "Get complete schema"},
                ],
                "config": {
                    "read_only": True,
                    "max_rows": 1000,
                    "allowed_schemas": ["public"],
                },
                "env_vars": {
                    "DATABASE_URL": str(settings.DATABASE_URL),
                },
            },
            {
                "name": "Calculator Server",
                "slug": "calculator",
                "description": "Simple calculator for basic math operations (testing/demo)",
                "server_type": "stdio",
                "command": "python",
                "args": ["-m", "src.mcp_servers.calculator_server"],
                "category": "utility",
                "author": "Platform Team",
                "status": "inactive",
                "visibility": "private",
                "tools": [
                    {"name": "add", "description": "Add two numbers"},
                    {"name": "subtract", "description": "Subtract two numbers"},
                    {"name": "multiply", "description": "Multiply two numbers"},
                    {"name": "divide", "description": "Divide two numbers"},
                    {"name": "power", "description": "Raise to power"},
                ],
                "config": {},
            },
        ]

        # Create servers
        for server_data in servers:
            # Check if already exists
            result = await db.execute(
                select(MCPServer).where(
                    MCPServer.tenant_id == tenant.id,
                    MCPServer.slug == server_data["slug"],
                    MCPServer.deleted_at.is_(None),
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  - MCP server '{server_data['name']}' already exists, skipping")
                continue

            # Create server
            server = MCPServer(tenant_id=tenant.id, **server_data)
            db.add(server)
            print(f"  ✓ Created MCP server: {server_data['name']}")

        await db.commit()

        print("\n✅ MCP server seeding complete!")
        print("\nNext steps:")
        print("1. Use the API to start servers: POST /v1/mcp/servers/{id}/discover")
        print("2. Execute tools: POST /v1/mcp/execute")
        print("3. Check execution logs: GET /v1/mcp/executions")


if __name__ == "__main__":
    asyncio.run(seed_mcp_servers())
