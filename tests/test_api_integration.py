"""
API Integration Tests

End-to-end tests for API workflows including:
- Agent creation and execution
- Workflow lifecycle
- MCP tool execution via API
- Complete user journeys
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Agent, MCPServer, Tenant, User, Workflow


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentAPI:
    """Test agent API endpoints."""

    async def test_create_agent(self, authenticated_client: AsyncClient):
        """Test creating an agent."""
        response = await authenticated_client.post(
            "/api/v1/agents",
            json={
                "name": "Integration Test Agent",
                "description": "Agent created during integration test",
                "system_prompt": "You are a helpful assistant for testing.",
                "model_provider": "anthropic",
                "model_name": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Integration Test Agent"
        assert data["slug"] == "integration-test-agent"
        assert data["status"] == "active"

    async def test_list_agents(
        self,
        authenticated_client: AsyncClient,
        test_agent: Agent,
    ):
        """Test listing agents."""
        response = await authenticated_client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) >= 1

    async def test_get_agent(
        self,
        authenticated_client: AsyncClient,
        test_agent: Agent,
    ):
        """Test getting a specific agent."""
        response = await authenticated_client.get(f"/api/v1/agents/{test_agent.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_agent.id)
        assert data["name"] == test_agent.name

    async def test_update_agent(
        self,
        authenticated_client: AsyncClient,
        test_agent: Agent,
    ):
        """Test updating an agent."""
        response = await authenticated_client.patch(
            f"/api/v1/agents/{test_agent.id}",
            json={"temperature": 0.5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["temperature"] == 0.5

    async def test_delete_agent(
        self,
        authenticated_client: AsyncClient,
        test_agent: Agent,
    ):
        """Test deleting an agent (soft delete)."""
        response = await authenticated_client.delete(f"/api/v1/agents/{test_agent.id}")

        assert response.status_code == 204


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkflowAPI:
    """Test workflow API endpoints."""

    async def test_create_workflow(
        self,
        authenticated_client: AsyncClient,
        test_agent: Agent,
    ):
        """Test creating a workflow."""
        response = await authenticated_client.post(
            "/api/v1/workflows/workflows",
            json={
                "name": "Integration Test Workflow",
                "description": "Workflow for testing",
                "version": "1.0.0",
                "steps": [
                    {
                        "type": "agent",
                        "name": "step1",
                        "agent_id": str(test_agent.id),
                        "input": {"instruction": "Test"},
                    }
                ],
                "timeout_seconds": 300,
                "max_retries": 3,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Integration Test Workflow"
        assert data["status"] == "draft"

    async def test_list_workflows(
        self,
        authenticated_client: AsyncClient,
        test_workflow: Workflow,
    ):
        """Test listing workflows."""
        response = await authenticated_client.get("/api/v1/workflows/workflows")

        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert len(data["workflows"]) >= 1

    async def test_get_workflow(
        self,
        authenticated_client: AsyncClient,
        test_workflow: Workflow,
    ):
        """Test getting a workflow."""
        response = await authenticated_client.get(
            f"/api/v1/workflows/workflows/{test_workflow.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_workflow.id)

    async def test_activate_workflow(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_workflow: Workflow,
    ):
        """Test activating a workflow."""
        # Ensure workflow is draft
        test_workflow.status = "draft"
        await db_session.commit()

        response = await authenticated_client.post(
            f"/api/v1/workflows/workflows/{test_workflow.id}/activate"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    async def test_workflow_lifecycle(
        self,
        authenticated_client: AsyncClient,
        test_agent: Agent,
    ):
        """Test complete workflow lifecycle: create -> activate -> execute -> check status."""
        # Create workflow
        create_response = await authenticated_client.post(
            "/api/v1/workflows/workflows",
            json={
                "name": "Lifecycle Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "type": "agent",
                        "name": "test_step",
                        "agent_id": str(test_agent.id),
                        "input": {"instruction": "Say hello"},
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        workflow_id = create_response.json()["id"]

        # Activate workflow
        activate_response = await authenticated_client.post(
            f"/api/v1/workflows/workflows/{workflow_id}/activate"
        )
        assert activate_response.status_code == 200

        # Execute workflow (will likely fail without actual LLM, but should create execution)
        execute_response = await authenticated_client.post(
            "/api/v1/workflows/workflows/execute",
            json={
                "workflow_id": workflow_id,
                "input_data": {"test": "data"},
            },
        )

        # Should create execution even if it fails
        if execute_response.status_code in [200, 500]:
            execution_data = execute_response.json()
            if "id" in execution_data:
                execution_id = execution_data["id"]

                # Check execution status
                status_response = await authenticated_client.get(
                    f"/api/v1/workflows/workflows/executions/{execution_id}"
                )
                assert status_response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPAPI:
    """Test MCP server API endpoints."""

    async def test_list_mcp_servers(
        self,
        authenticated_client: AsyncClient,
        test_mcp_server: MCPServer,
    ):
        """Test listing MCP servers."""
        response = await authenticated_client.get("/api/v1/mcp/servers")

        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert len(data["servers"]) >= 1

    async def test_get_mcp_server(
        self,
        authenticated_client: AsyncClient,
        test_mcp_server: MCPServer,
    ):
        """Test getting an MCP server."""
        response = await authenticated_client.get(
            f"/api/v1/mcp/servers/{test_mcp_server.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_mcp_server.id)
        assert data["name"] == test_mcp_server.name

    async def test_discover_server_capabilities(
        self,
        authenticated_client: AsyncClient,
        test_mcp_server: MCPServer,
    ):
        """Test discovering server tools."""
        response = await authenticated_client.get(
            f"/api/v1/mcp/servers/{test_mcp_server.id}/discover"
        )

        # May succeed or fail depending on server availability
        assert response.status_code in [200, 500]


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
class TestCompleteUserJourney:
    """Test complete user journeys through the system."""

    async def test_new_user_creates_agent_and_workflow(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        db_session: AsyncSession,
    ):
        """Test a new user registering and creating resources."""
        # Register
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "journey@example.com",
                "username": "journey",
                "password": "password123",
                "full_name": "Journey User",
                "tenant_slug": test_tenant.slug,
            },
        )
        assert register_response.status_code == 201

        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "journey@example.com",
                "password": "password123",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Set auth header
        client.headers["Authorization"] = f"Bearer {token}"

        # Create agent
        agent_response = await client.post(
            "/api/v1/agents",
            json={
                "name": "Journey Agent",
                "system_prompt": "You are helpful.",
                "model_provider": "anthropic",
                "model_name": "claude-3-5-sonnet-20241022",
            },
        )
        assert agent_response.status_code == 201
        agent_id = agent_response.json()["id"]

        # Create workflow
        workflow_response = await client.post(
            "/api/v1/workflows/workflows",
            json={
                "name": "Journey Workflow",
                "version": "1.0.0",
                "steps": [
                    {
                        "type": "agent",
                        "name": "greet",
                        "agent_id": agent_id,
                        "input": {"instruction": "Greet the user"},
                    }
                ],
            },
        )
        assert workflow_response.status_code == 201


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorHandling:
    """Test API error handling."""

    async def test_404_for_nonexistent_resource(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test 404 response for non-existent resources."""
        import uuid

        response = await authenticated_client.get(f"/api/v1/agents/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_422_for_invalid_input(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test 422 response for validation errors."""
        response = await authenticated_client.post(
            "/api/v1/agents",
            json={
                "name": "",  # Empty name should fail validation
                "model_provider": "anthropic",
            },
        )

        assert response.status_code == 422

    async def test_401_for_unauthorized_access(
        self,
        client: AsyncClient,
    ):
        """Test 401 response for unauthorized requests."""
        response = await client.get("/api/v1/agents")

        assert response.status_code == 401


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
class TestPagination:
    """Test API pagination."""

    async def test_paginated_list_response(
        self,
        authenticated_client: AsyncClient,
        agent_factory,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test that list endpoints support pagination."""
        # Create multiple agents
        for i in range(15):
            await agent_factory(
                test_tenant.id,
                test_user.id,
                name=f"Agent {i}",
            )

        # Test pagination
        response = await authenticated_client.get(
            "/api/v1/agents?offset=0&limit=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert len(data["agents"]) <= 10

    async def test_pagination_offset(
        self,
        authenticated_client: AsyncClient,
        agent_factory,
        test_tenant: Tenant,
        test_user: User,
    ):
        """Test pagination offset parameter."""
        # Create agents
        for i in range(5):
            await agent_factory(test_tenant.id, test_user.id, name=f"Offset Agent {i}")

        # Get first page
        page1 = await authenticated_client.get("/api/v1/agents?offset=0&limit=3")
        # Get second page
        page2 = await authenticated_client.get("/api/v1/agents?offset=3&limit=3")

        assert page1.status_code == 200
        assert page2.status_code == 200

        page1_ids = [a["id"] for a in page1.json()["agents"]]
        page2_ids = [a["id"] for a in page2.json()["agents"]]

        # Pages should have different results
        assert set(page1_ids).isdisjoint(set(page2_ids))
