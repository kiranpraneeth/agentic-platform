"""
Seed Workflow Templates

Creates pre-built workflow templates for common use cases.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from src.core.config import settings
from src.db.models import Agent, Tenant, User, Workflow
from src.db.session import AsyncSessionLocal


async def seed_workflow_templates():
    """Seed workflow templates."""
    async with AsyncSessionLocal() as db:
        # Get demo tenant
        result = await db.execute(select(Tenant).where(Tenant.slug == "demo-tenant"))
        tenant = result.scalar_one_or_none()
        if not tenant:
            print("Demo tenant not found. Run seed_dev_data.py first.")
            return

        # Get first user for tenant (or None if no users yet)
        result = await db.execute(
            select(User).where(User.tenant_id == tenant.id).limit(1)
        )
        user = result.scalar_one_or_none()
        user_id = user.id if user else None

        # Get demo agents
        result = await db.execute(select(Agent).where(Agent.tenant_id == tenant.id))
        agents = result.scalars().all()
        if not agents:
            print("No agents found. Create agents first.")
            return

        agent = agents[0]  # Use first agent for examples

        print(f"Creating workflow templates for tenant: {tenant.name}")
        print(f"Using agent: {agent.name} ({agent.id})")
        print(f"Created by user: {user_id or 'None'}")

        # Template 1: Simple Sequential Workflow
        print("\n1. Creating Simple Sequential Workflow...")
        workflow1_name = "Simple Sequential Analysis"
        if not await _workflow_exists(db, tenant.id, workflow1_name):
            workflow1 = Workflow(
                tenant_id=tenant.id,
                name=workflow1_name,
                slug=slugify(workflow1_name),
                description="A simple workflow that performs analysis in sequential steps",
                version="1.0.0",
                steps=[
                    {
                        "type": "agent",
                        "name": "initial_analysis",
                        "agent_id": str(agent.id),
                        "input": {
                            "instruction": "Analyze the following data: {input.data}",
                            "context": {},
                        },
                        "output_mapping": {"analysis_result": "$.response"},
                    },
                    {
                        "type": "agent",
                        "name": "generate_summary",
                        "agent_id": str(agent.id),
                        "input": {
                            "instruction": "Create a summary of this analysis: {initial_analysis.analysis_result}",
                            "context": {},
                        },
                        "output_mapping": {"summary": "$.response"},
                    },
                ],
                triggers=[{"type": "manual", "enabled": True, "config": {}}],
                timeout_seconds=1800,
                max_retries=3,
                retry_strategy="exponential",
                status="active",
                tags=["example", "sequential", "analysis"],
                category="examples",
                created_by=user_id,
            )
            db.add(workflow1)
            print(f"   ✓ Created: {workflow1_name}")
        else:
            print(f"   ⊘ Already exists: {workflow1_name}")

        # Template 2: Parallel Execution Workflow
        print("\n2. Creating Parallel Execution Workflow...")
        workflow2_name = "Parallel Research Workflow"
        if not await _workflow_exists(db, tenant.id, workflow2_name):
            workflow2 = Workflow(
                tenant_id=tenant.id,
                name=workflow2_name,
                slug=slugify(workflow2_name),
                description="Execute multiple research tasks in parallel and synthesize results",
                version="1.0.0",
                steps=[
                    {
                        "type": "parallel",
                        "name": "parallel_research",
                        "steps": [
                            {
                                "type": "agent",
                                "name": "research_topic_a",
                                "agent_id": str(agent.id),
                                "input": {
                                    "instruction": "Research topic A: {input.topic_a}",
                                    "context": {},
                                },
                            },
                            {
                                "type": "agent",
                                "name": "research_topic_b",
                                "agent_id": str(agent.id),
                                "input": {
                                    "instruction": "Research topic B: {input.topic_b}",
                                    "context": {},
                                },
                            },
                            {
                                "type": "agent",
                                "name": "research_topic_c",
                                "agent_id": str(agent.id),
                                "input": {
                                    "instruction": "Research topic C: {input.topic_c}",
                                    "context": {},
                                },
                            },
                        ],
                        "wait_for": "all",
                    },
                    {
                        "type": "agent",
                        "name": "synthesize_results",
                        "agent_id": str(agent.id),
                        "input": {
                            "instruction": "Synthesize these research findings into a comprehensive report",
                            "context": {
                                "research_a": "{parallel_research.step_0}",
                                "research_b": "{parallel_research.step_1}",
                                "research_c": "{parallel_research.step_2}",
                            },
                        },
                    },
                ],
                triggers=[{"type": "manual", "enabled": True, "config": {}}],
                timeout_seconds=3600,
                max_retries=2,
                retry_strategy="exponential",
                status="active",
                tags=["example", "parallel", "research"],
                category="examples",
                created_by=user_id,
            )
            db.add(workflow2)
            print(f"   ✓ Created: {workflow2_name}")
        else:
            print(f"   ⊘ Already exists: {workflow2_name}")

        # Template 3: Conditional Workflow
        print("\n3. Creating Conditional Workflow...")
        workflow3_name = "Conditional Processing Workflow"
        if not await _workflow_exists(db, tenant.id, workflow3_name):
            workflow3 = Workflow(
                tenant_id=tenant.id,
                name=workflow3_name,
                slug=slugify(workflow3_name),
                description="Route processing based on classification results",
                version="1.0.0",
                steps=[
                    {
                        "type": "agent",
                        "name": "classify_request",
                        "agent_id": str(agent.id),
                        "input": {
                            "instruction": "Classify this request and provide a confidence score (0-1): {input.request}",
                            "context": {},
                        },
                        "output_mapping": {"confidence": "$.confidence", "category": "$.category"},
                    },
                    {
                        "type": "conditional",
                        "name": "route_based_on_confidence",
                        "condition": "$.classify_request.confidence > 0.8",
                        "if_true": {
                            "type": "agent",
                            "name": "high_confidence_processing",
                            "agent_id": str(agent.id),
                            "input": {
                                "instruction": "Process high-confidence request: {input.request}",
                                "context": {"classification": "{classify_request}"},
                            },
                        },
                        "if_false": {
                            "type": "agent",
                            "name": "low_confidence_processing",
                            "agent_id": str(agent.id),
                            "input": {
                                "instruction": "Process low-confidence request with extra validation: {input.request}",
                                "context": {"classification": "{classify_request}"},
                            },
                        },
                    },
                ],
                triggers=[{"type": "manual", "enabled": True, "config": {}}],
                timeout_seconds=1800,
                max_retries=3,
                retry_strategy="exponential",
                status="active",
                tags=["example", "conditional", "routing"],
                category="examples",
                created_by=user_id,
            )
            db.add(workflow3)
            print(f"   ✓ Created: {workflow3_name}")
        else:
            print(f"   ⊘ Already exists: {workflow3_name}")

        # Template 4: Multi-Step Data Pipeline
        print("\n4. Creating Multi-Step Data Pipeline...")
        workflow4_name = "Data Processing Pipeline"
        if not await _workflow_exists(db, tenant.id, workflow4_name):
            workflow4 = Workflow(
                tenant_id=tenant.id,
                name=workflow4_name,
                slug=slugify(workflow4_name),
                description="Extract, transform, validate, and process data",
                version="1.0.0",
                steps=[
                    {
                        "type": "agent",
                        "name": "extract_data",
                        "agent_id": str(agent.id),
                        "input": {
                            "instruction": "Extract data from source: {input.source}",
                            "context": {},
                        },
                        "max_retries": 3,
                    },
                    {
                        "type": "agent",
                        "name": "transform_data",
                        "agent_id": str(agent.id),
                        "input": {
                            "instruction": "Transform extracted data to target format",
                            "context": {"raw_data": "{extract_data.response}"},
                        },
                    },
                    {
                        "type": "agent",
                        "name": "validate_data",
                        "agent_id": str(agent.id),
                        "input": {
                            "instruction": "Validate transformed data for completeness and accuracy",
                            "context": {"transformed_data": "{transform_data.response}"},
                        },
                        "output_mapping": {"is_valid": "$.is_valid", "validation_result": "$.result"},
                    },
                    {
                        "type": "conditional",
                        "name": "check_validation",
                        "condition": "$.validate_data.is_valid == true",
                        "if_true": {
                            "type": "agent",
                            "name": "process_valid_data",
                            "agent_id": str(agent.id),
                            "input": {
                                "instruction": "Process validated data",
                                "context": {"data": "{transform_data.response}"},
                            },
                        },
                        "if_false": {
                            "type": "agent",
                            "name": "handle_invalid_data",
                            "agent_id": str(agent.id),
                            "input": {
                                "instruction": "Handle data validation failure",
                                "context": {
                                    "validation_errors": "{validate_data.validation_result}"
                                },
                            },
                        },
                    },
                ],
                triggers=[{"type": "manual", "enabled": True, "config": {}}],
                timeout_seconds=3600,
                max_retries=2,
                retry_strategy="exponential",
                status="active",
                tags=["example", "pipeline", "etl"],
                category="examples",
                created_by=user_id,
            )
            db.add(workflow4)
            print(f"   ✓ Created: {workflow4_name}")
        else:
            print(f"   ⊘ Already exists: {workflow4_name}")

        # Template 5: HTTP Integration Workflow
        print("\n5. Creating HTTP Integration Workflow...")
        workflow5_name = "API Integration Workflow"
        if not await _workflow_exists(db, tenant.id, workflow5_name):
            workflow5 = Workflow(
                tenant_id=tenant.id,
                name=workflow5_name,
                slug=slugify(workflow5_name),
                description="Fetch data from API and process it",
                version="1.0.0",
                steps=[
                    {
                        "type": "http",
                        "name": "fetch_from_api",
                        "method": "GET",
                        "url": "{input.api_url}",
                        "headers": {"Content-Type": "application/json"},
                    },
                    {
                        "type": "agent",
                        "name": "process_api_response",
                        "agent_id": str(agent.id),
                        "input": {
                            "instruction": "Process and analyze this API response",
                            "context": {"api_data": "{fetch_from_api.body}"},
                        },
                    },
                ],
                triggers=[{"type": "manual", "enabled": True, "config": {}}],
                timeout_seconds=1800,
                max_retries=3,
                retry_strategy="linear",
                status="active",
                tags=["example", "http", "api", "integration"],
                category="examples",
                created_by=user_id,
            )
            db.add(workflow5)
            print(f"   ✓ Created: {workflow5_name}")
        else:
            print(f"   ⊘ Already exists: {workflow5_name}")

        # Commit all workflows
        await db.commit()

        # Get workflow count
        result = await db.execute(
            select(Workflow).where(Workflow.tenant_id == tenant.id, Workflow.category == "examples")
        )
        workflows = result.scalars().all()

        print(f"\n✅ Workflow templates seeded successfully!")
        print(f"   Total example workflows: {len(workflows)}")
        print(f"   Tenant: {tenant.name}")
        print(f"\n   You can now execute these workflows via the API:")
        print(f"   POST /api/v1/workflows/execute")
        print(f"   GET  /api/v1/workflows?category=examples")


async def _workflow_exists(db: AsyncSession, tenant_id, name: str) -> bool:
    """Check if workflow already exists."""
    result = await db.execute(
        select(Workflow).where(
            Workflow.tenant_id == tenant_id,
            Workflow.name == name,
            Workflow.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


if __name__ == "__main__":
    print("=" * 70)
    print("Seeding Workflow Templates")
    print("=" * 70)
    asyncio.run(seed_workflow_templates())
    print("\n" + "=" * 70)
