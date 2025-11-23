"""Pytest configuration and fixtures."""

import asyncio
import uuid
from typing import AsyncGenerator, Callable, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.db.base import Base
from src.db.models import Agent, MCPServer, Tenant, User, Workflow
from src.db.session import get_db
from src.main import app
from src.core.security import create_access_token, get_password_hash

# Test database URL - ensure we use asyncpg driver
TEST_DATABASE_URL = str(settings.DATABASE_URL).replace(
    "/agentic_db", "/agentic_test_db"
).replace("postgresql://", "postgresql+asyncpg://").replace("postgresql+psycopg2://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        settings={"test_mode": True},
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test user."""
    user = User(
        tenant_id=test_tenant.id,
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_agent(db_session: AsyncSession, test_tenant: Tenant, test_user: User) -> Agent:
    """Create a test agent."""
    agent = Agent(
        tenant_id=test_tenant.id,
        name="Test Agent",
        slug="test-agent",
        description="A test agent for automated testing",
        system_prompt="You are a helpful test assistant.",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=1000,
        status="active",
        created_by=test_user.id,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest_asyncio.fixture(scope="function")
async def test_workflow(
    db_session: AsyncSession, test_tenant: Tenant, test_user: User, test_agent: Agent
) -> Workflow:
    """Create a test workflow."""
    workflow = Workflow(
        tenant_id=test_tenant.id,
        name="Test Workflow",
        slug="test-workflow",
        description="A test workflow",
        version="1.0.0",
        steps=[
            {
                "type": "agent",
                "name": "test_step",
                "agent_id": str(test_agent.id),
                "input": {"instruction": "Test instruction"},
            }
        ],
        triggers=[{"type": "manual", "enabled": True, "config": {}}],
        timeout_seconds=300,
        max_retries=3,
        retry_strategy="exponential",
        status="active",
        created_by=test_user.id,
    )
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)
    return workflow


@pytest_asyncio.fixture(scope="function")
async def test_mcp_server(db_session: AsyncSession, test_tenant: Tenant) -> MCPServer:
    """Create a test MCP server."""
    server = MCPServer(
        tenant_id=test_tenant.id,
        name="Test Calculator",
        slug="test-calculator",
        description="Test calculator server",
        server_type="stdio",
        command="python",
        args=["-m", "src.mcp_servers.calculator_server"],
        status="active",
        tools=[
            {
                "name": "add",
                "description": "Add two numbers",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            }
        ],
    )
    db_session.add(server)
    await db_session.commit()
    await db_session.refresh(server)
    return server


@pytest.fixture(scope="function")
def access_token(test_user: User) -> str:
    """Create an access token for test user."""
    return create_access_token({"sub": str(test_user.id)})


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: AsyncClient, access_token: str) -> AsyncClient:
    """Create authenticated test client."""
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client


# Factory fixtures


@pytest_asyncio.fixture
async def tenant_factory(db_session: AsyncSession) -> Callable:
    """Factory for creating test tenants."""

    async def _create_tenant(name: str = None, slug: str = None) -> Tenant:
        name = name or f"Tenant-{uuid.uuid4().hex[:8]}"
        slug = slug or name.lower().replace(" ", "-")

        tenant = Tenant(name=name, slug=slug, settings={})
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)
        return tenant

    return _create_tenant


@pytest_asyncio.fixture
async def user_factory(db_session: AsyncSession) -> Callable:
    """Factory for creating test users."""

    async def _create_user(
        tenant_id: uuid.UUID, email: str = None, password: str = "password123"
    ) -> User:
        email = email or f"user-{uuid.uuid4().hex[:8]}@example.com"

        user = User(
            tenant_id=tenant_id,
            email=email,
            username=email.split("@")[0],
            hashed_password=get_password_hash(password),
            full_name="Test User",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create_user


@pytest_asyncio.fixture
async def agent_factory(db_session: AsyncSession) -> Callable:
    """Factory for creating test agents."""

    async def _create_agent(
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str = None,
        **kwargs,
    ) -> Agent:
        name = name or f"Agent-{uuid.uuid4().hex[:8]}"

        agent = Agent(
            tenant_id=tenant_id,
            name=name,
            slug=name.lower().replace(" ", "-"),
            description=kwargs.get("description", "Test agent"),
            system_prompt=kwargs.get("system_prompt", "You are a test assistant."),
            model_provider=kwargs.get("model_provider", "anthropic"),
            model_name=kwargs.get("model_name", "claude-3-5-sonnet-20241022"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
            status=kwargs.get("status", "active"),
            created_by=user_id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)
        return agent

    return _create_agent


# Test markers


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "workflow: Workflow engine tests")
    config.addinivalue_line("markers", "mcp: MCP server tests")
    config.addinivalue_line("markers", "rag: RAG system tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
