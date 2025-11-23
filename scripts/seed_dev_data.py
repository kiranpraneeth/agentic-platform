"""Seed development data - create default tenant and admin user."""

import asyncio
import uuid

from sqlalchemy import select

from src.core.security import get_password_hash
from src.db.models import Agent, Tenant, User
from src.db.session import AsyncSessionLocal


async def seed_dev_data() -> None:
    """Create development seed data."""
    async with AsyncSessionLocal() as session:
        # Check if tenant already exists
        result = await session.execute(select(Tenant).where(Tenant.slug == "demo-tenant"))
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            print("Demo tenant already exists. Skipping seed data.")
            return

        print("Creating development seed data...")

        # Create default tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Demo Tenant",
            slug="demo-tenant",
            email="admin@demo.com",
            contact_name="Admin User",
            status="active",
            plan_type="pro",
            max_agents=50,
            max_requests_per_day=100000,
            max_tokens_per_month=10000000,
            settings={},
            extra_metadata={"created_by": "seed_script"},
        )
        session.add(tenant)
        await session.flush()

        # Create admin user
        admin_user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="admin@demo.com",
            username="admin",
            password_hash=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            status="active",
            email_verified=True,
            role="admin",
            permissions={"all": True},
            extra_metadata={"created_by": "seed_script"},
        )
        session.add(admin_user)

        # Create sample agent
        sample_agent = Agent(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Customer Support Agent",
            slug="customer-support",
            description="A helpful customer support assistant that can answer questions and help with issues.",
            status="active",
            model_provider="anthropic",
            model_name="claude-sonnet-4-5",
            system_prompt="You are a friendly and professional customer support agent. "
            "Help users with their questions and issues in a clear and concise manner. "
            "Be empathetic and provide actionable solutions.",
            temperature=0.7,
            max_tokens=4096,
            capabilities=["conversation", "problem_solving"],
            tools=[],
            timeout_seconds=300,
            max_iterations=10,
            memory_enabled=True,
            version="1.0.0",
            tags=["support", "customer-service"],
            config={},
            extra_metadata={"created_by": "seed_script"},
        )
        session.add(sample_agent)

        await session.commit()

        print("✅ Development seed data created successfully!")
        print(f"   Tenant: {tenant.name} ({tenant.slug})")
        print(f"   Admin User: {admin_user.email} / password: admin123")
        print(f"   Sample Agent: {sample_agent.name} ({sample_agent.id})")


if __name__ == "__main__":
    asyncio.run(seed_dev_data())
