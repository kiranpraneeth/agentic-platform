"""
Workflow Engine Service

Orchestrates multi-step workflows with support for:
- Sequential and parallel execution
- Conditional branching
- Agent coordination
- MCP tool integration
- Error handling and retries
- State management
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Agent,
    AgentMessage,
    AgentTask,
    Workflow,
    WorkflowExecution,
    WorkflowStepExecution,
)
from src.services.agent_executor import AgentExecutor
from src.services.mcp_client import MCPClient


class WorkflowEngine:
    """
    Workflow execution engine.

    Executes workflows end-to-end with support for:
    - Multi-step orchestration
    - Parallel execution
    - Conditional branching
    - Agent and MCP tool integration
    - Error handling and retries
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        """Initialize workflow engine."""
        self.db = db
        self.tenant_id = tenant_id
        self.agent_executor = AgentExecutor(db)
        self.mcp_client = MCPClient(db, tenant_id)

    async def execute_workflow(
        self,
        workflow_id: uuid.UUID,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """
        Execute a workflow end-to-end.

        Args:
            workflow_id: Workflow to execute
            input_data: Input data for the workflow
            context: Additional context (optional)

        Returns:
            WorkflowExecution with results
        """
        # Load workflow definition
        result = await self.db.execute(
            select(Workflow).where(
                Workflow.id == workflow_id,
                Workflow.tenant_id == self.tenant_id,
                Workflow.deleted_at.is_(None),
            )
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != "active":
            raise ValueError(f"Workflow {workflow_id} is not active")

        # Create workflow execution
        execution = WorkflowExecution(
            tenant_id=self.tenant_id,
            workflow_id=workflow_id,
            input_data=input_data,
            context=context or {},
            status="running",
            current_step="",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        try:
            # Execute workflow steps
            output_data = await self._execute_steps(
                workflow=workflow,
                execution=execution,
                steps=workflow.steps,
                workflow_context={"input": input_data, **(context or {})},
            )

            # Mark workflow as completed
            execution.status = "completed"
            execution.output_data = output_data
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_seconds = int(
                (execution.completed_at - execution.started_at).total_seconds()
            )

        except Exception as e:
            # Mark workflow as failed
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_seconds = int(
                (execution.completed_at - execution.started_at).total_seconds()
            )
            raise

        finally:
            await self.db.commit()
            await self.db.refresh(execution)

        return execution

    async def _execute_steps(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        steps: list[dict[str, Any]],
        workflow_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a list of workflow steps.

        Args:
            workflow: Workflow definition
            execution: Workflow execution instance
            steps: List of step definitions
            workflow_context: Current workflow context

        Returns:
            Final output data
        """
        for step in steps:
            step_type = step.get("type")
            step_name = step.get("name", "unnamed_step")

            # Update current step
            execution.current_step = step_name
            await self.db.commit()

            # Execute step based on type
            if step_type == "agent":
                result = await self._execute_agent_step(execution, step, workflow_context)
            elif step_type == "mcp_tool":
                result = await self._execute_mcp_tool_step(execution, step, workflow_context)
            elif step_type == "parallel":
                result = await self._execute_parallel_step(
                    workflow, execution, step, workflow_context
                )
            elif step_type == "conditional":
                result = await self._execute_conditional_step(
                    workflow, execution, step, workflow_context
                )
            elif step_type == "http":
                result = await self._execute_http_step(execution, step, workflow_context)
            else:
                raise ValueError(f"Unknown step type: {step_type}")

            # Update workflow context with step result
            workflow_context[step_name] = result

        return workflow_context

    async def _execute_agent_step(
        self,
        execution: WorkflowExecution,
        step: dict[str, Any],
        workflow_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an agent step."""
        step_name = step.get("name", "unnamed_step")
        agent_id = uuid.UUID(step["agent_id"])

        # Create step execution
        step_execution = WorkflowStepExecution(
            tenant_id=self.tenant_id,
            workflow_execution_id=execution.id,
            step_name=step_name,
            step_type="agent",
            agent_id=agent_id,
            input_data=step.get("input", {}),
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step_execution)
        await self.db.commit()
        await self.db.refresh(step_execution)

        try:
            # Resolve input data (replace template variables)
            input_data = self._resolve_template_vars(step.get("input", {}), workflow_context)

            # Load agent
            result = await self.db.execute(
                select(Agent).where(
                    Agent.id == agent_id,
                    Agent.tenant_id == self.tenant_id,
                    Agent.deleted_at.is_(None),
                )
            )
            agent = result.scalar_one_or_none()
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")

            # Execute agent
            instruction = input_data.get("instruction", "")
            context_str = json.dumps(input_data.get("context", {}))

            # Create agent task
            task = AgentTask(
                tenant_id=self.tenant_id,
                agent_id=agent_id,
                workflow_execution_id=execution.id,
                task_type="execute",
                instruction=instruction,
                context=input_data.get("context", {}),
                status="in_progress",
                priority=step.get("priority", 5),
                assigned_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)

            # Execute using agent executor
            agent_response = await self.agent_executor.execute_agent(
                agent=agent,
                user_message=instruction,
                context=context_str,
                conversation_id=None,  # Workflow execution, not a conversation
            )

            # Update task
            task.status = "completed"
            task.result = {"response": agent_response}
            task.completed_at = datetime.now(timezone.utc)

            # Update step execution
            step_execution.status = "completed"
            step_execution.output_data = {"response": agent_response, "task_id": str(task.id)}
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )

            await self.db.commit()

            # Apply output mapping if specified
            output = step_execution.output_data
            if "output_mapping" in step:
                output = self._apply_output_mapping(output, step["output_mapping"])

            return output

        except Exception as e:
            # Update task if it exists
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now(timezone.utc)

            # Update step execution
            step_execution.status = "failed"
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()

            # Handle retry logic
            if step_execution.retry_count < step.get("max_retries", 0):
                step_execution.retry_count += 1
                await self.db.commit()
                # Retry the step
                return await self._execute_agent_step(execution, step, workflow_context)

            raise

    async def _execute_mcp_tool_step(
        self,
        execution: WorkflowExecution,
        step: dict[str, Any],
        workflow_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an MCP tool step."""
        step_name = step.get("name", "unnamed_step")
        server_id = uuid.UUID(step["server_id"])
        tool_name = step["tool_name"]

        # Create step execution
        step_execution = WorkflowStepExecution(
            tenant_id=self.tenant_id,
            workflow_execution_id=execution.id,
            step_name=step_name,
            step_type="mcp_tool",
            input_data=step.get("input", {}),
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step_execution)
        await self.db.commit()
        await self.db.refresh(step_execution)

        try:
            # Resolve input data
            tool_input = self._resolve_template_vars(step.get("input", {}), workflow_context)

            # Execute MCP tool
            result = await self.mcp_client.execute_tool(
                server_id=server_id,
                tool_name=tool_name,
                tool_input=tool_input,
                conversation_id=None,
            )

            # Update step execution
            step_execution.status = "completed"
            step_execution.output_data = result
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()

            return result

        except Exception as e:
            step_execution.status = "failed"
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()

            # Handle retry logic
            if step_execution.retry_count < step.get("max_retries", 0):
                step_execution.retry_count += 1
                await self.db.commit()
                return await self._execute_mcp_tool_step(execution, step, workflow_context)

            raise

    async def _execute_parallel_step(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        step: dict[str, Any],
        workflow_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute multiple steps in parallel."""
        step_name = step.get("name", "unnamed_step")
        parallel_steps = step.get("steps", [])
        wait_for = step.get("wait_for", "all")  # all, any, count:N

        # Create step execution
        step_execution = WorkflowStepExecution(
            tenant_id=self.tenant_id,
            workflow_execution_id=execution.id,
            step_name=step_name,
            step_type="parallel",
            input_data={"parallel_steps": parallel_steps, "wait_for": wait_for},
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step_execution)
        await self.db.commit()
        await self.db.refresh(step_execution)

        try:
            # Execute all steps in parallel
            tasks = []
            for parallel_step in parallel_steps:
                task = asyncio.create_task(
                    self._execute_single_step(workflow, execution, parallel_step, workflow_context)
                )
                tasks.append(task)

            # Wait based on wait_for strategy
            if wait_for == "all":
                results = await asyncio.gather(*tasks, return_exceptions=True)
            elif wait_for == "any":
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                results = [task.result() for task in done]
            elif wait_for.startswith("count:"):
                count = int(wait_for.split(":")[1])
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                while len(done) < count and pending:
                    new_done, pending = await asyncio.wait(
                        pending, return_when=asyncio.FIRST_COMPLETED
                    )
                    done.update(new_done)
                # Cancel remaining tasks
                for task in pending:
                    task.cancel()
                results = [task.result() for task in done]
            else:
                results = await asyncio.gather(*tasks, return_exceptions=True)

            # Combine results
            output_data = {
                f"step_{i}": result
                for i, result in enumerate(results)
                if not isinstance(result, Exception)
            }

            # Check for errors
            errors = [result for result in results if isinstance(result, Exception)]
            if errors and wait_for == "all":
                raise Exception(f"Parallel execution failed: {errors}")

            # Update step execution
            step_execution.status = "completed"
            step_execution.output_data = output_data
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()

            return output_data

        except Exception as e:
            step_execution.status = "failed"
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()
            raise

    async def _execute_conditional_step(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        step: dict[str, Any],
        workflow_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a conditional step."""
        step_name = step.get("name", "unnamed_step")
        condition = step.get("condition", "")

        # Create step execution
        step_execution = WorkflowStepExecution(
            tenant_id=self.tenant_id,
            workflow_execution_id=execution.id,
            step_name=step_name,
            step_type="conditional",
            input_data={"condition": condition},
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step_execution)
        await self.db.commit()
        await self.db.refresh(step_execution)

        try:
            # Evaluate condition
            condition_result = self._evaluate_condition(condition, workflow_context)

            # Execute appropriate branch
            if condition_result:
                branch_step = step.get("if_true")
                branch_name = "true"
            else:
                branch_step = step.get("if_false")
                branch_name = "false"

            if branch_step:
                result = await self._execute_single_step(
                    workflow, execution, branch_step, workflow_context
                )
            else:
                result = {"skipped": True, "branch": branch_name}

            # Update step execution
            step_execution.status = "completed"
            step_execution.output_data = {
                "condition_result": condition_result,
                "branch_taken": branch_name,
                "result": result,
            }
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()

            return step_execution.output_data

        except Exception as e:
            step_execution.status = "failed"
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()
            raise

    async def _execute_http_step(
        self,
        execution: WorkflowExecution,
        step: dict[str, Any],
        workflow_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an HTTP request step."""
        step_name = step.get("name", "unnamed_step")

        # Create step execution
        step_execution = WorkflowStepExecution(
            tenant_id=self.tenant_id,
            workflow_execution_id=execution.id,
            step_name=step_name,
            step_type="http",
            input_data=step,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step_execution)
        await self.db.commit()
        await self.db.refresh(step_execution)

        try:
            import aiohttp

            # Resolve template variables
            method = step.get("method", "GET")
            url = self._resolve_template_string(step.get("url", ""), workflow_context)
            headers = self._resolve_template_vars(step.get("headers", {}), workflow_context)
            body = self._resolve_template_vars(step.get("body", {}), workflow_context)

            # Make HTTP request
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method, url=url, headers=headers, json=body
                ) as response:
                    result = {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body": await response.json() if response.content_type == "application/json" else await response.text(),
                    }

            # Update step execution
            step_execution.status = "completed"
            step_execution.output_data = result
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()

            return result

        except Exception as e:
            step_execution.status = "failed"
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.now(timezone.utc)
            step_execution.duration_seconds = int(
                (step_execution.completed_at - step_execution.started_at).total_seconds()
            )
            await self.db.commit()
            raise

    async def _execute_single_step(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        step: dict[str, Any],
        workflow_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single step (helper for parallel execution)."""
        step_type = step.get("type")

        if step_type == "agent":
            return await self._execute_agent_step(execution, step, workflow_context)
        elif step_type == "mcp_tool":
            return await self._execute_mcp_tool_step(execution, step, workflow_context)
        elif step_type == "http":
            return await self._execute_http_step(execution, step, workflow_context)
        else:
            raise ValueError(f"Unknown step type: {step_type}")

    def _resolve_template_vars(
        self, data: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve template variables in data using context."""
        if isinstance(data, dict):
            return {k: self._resolve_template_vars(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_template_vars(item, context) for item in data]
        elif isinstance(data, str):
            return self._resolve_template_string(data, context)
        else:
            return data

    def _resolve_template_string(self, template: str, context: dict[str, Any]) -> str:
        """Resolve template string with context variables."""
        # Simple template variable resolution: {variable_name}
        import re

        def replace_var(match):
            var_name = match.group(1)
            # Support nested access like {step1.result.value}
            parts = var_name.split(".")
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return match.group(0)  # Return original if not found
            return str(value) if value is not None else match.group(0)

        return re.sub(r"\{([^}]+)\}", replace_var, template)

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """
        Evaluate a condition expression.

        Supports JSONPath-like syntax: $.step_name.field > value
        """
        # Simple condition evaluation
        # Format: $.step_name.field operator value
        # Example: $.classify_query.confidence > 0.8

        import re

        # Parse condition
        match = re.match(r"\$\.(\S+)\s*([><=!]+)\s*(.+)", condition.strip())
        if not match:
            raise ValueError(f"Invalid condition format: {condition}")

        path = match.group(1)
        operator = match.group(2)
        expected_value_str = match.group(3).strip()

        # Get actual value from context
        parts = path.split(".")
        actual_value = context
        for part in parts:
            if isinstance(actual_value, dict):
                actual_value = actual_value.get(part)
            else:
                actual_value = None
                break

        # Convert expected value
        try:
            if expected_value_str.lower() == "true":
                expected_value = True
            elif expected_value_str.lower() == "false":
                expected_value = False
            elif expected_value_str.lower() == "null":
                expected_value = None
            elif expected_value_str.startswith('"') and expected_value_str.endswith('"'):
                expected_value = expected_value_str[1:-1]
            else:
                expected_value = float(expected_value_str)
        except ValueError:
            expected_value = expected_value_str

        # Evaluate operator
        if operator == ">":
            return actual_value > expected_value
        elif operator == "<":
            return actual_value < expected_value
        elif operator == ">=":
            return actual_value >= expected_value
        elif operator == "<=":
            return actual_value <= expected_value
        elif operator == "==":
            return actual_value == expected_value
        elif operator == "!=":
            return actual_value != expected_value
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def _apply_output_mapping(
        self, data: dict[str, Any], mapping: dict[str, str]
    ) -> dict[str, Any]:
        """Apply output mapping to extract specific fields."""
        result = {}
        for output_key, path in mapping.items():
            # JSONPath-like extraction: $.output.content
            if path.startswith("$."):
                parts = path[2:].split(".")
                value = data
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = None
                        break
                result[output_key] = value
            else:
                result[output_key] = data.get(path)
        return result

    async def cancel_workflow(self, execution_id: uuid.UUID) -> WorkflowExecution:
        """Cancel a running workflow."""
        result = await self.db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.id == execution_id,
                WorkflowExecution.tenant_id == self.tenant_id,
            )
        )
        execution = result.scalar_one_or_none()
        if not execution:
            raise ValueError(f"Workflow execution {execution_id} not found")

        if execution.status not in ["pending", "running"]:
            raise ValueError(f"Cannot cancel workflow in status: {execution.status}")

        execution.status = "cancelled"
        execution.completed_at = datetime.now(timezone.utc)
        execution.duration_seconds = int(
            (execution.completed_at - execution.started_at).total_seconds()
        )

        await self.db.commit()
        await self.db.refresh(execution)

        return execution

    async def get_execution_status(self, execution_id: uuid.UUID) -> dict[str, Any]:
        """Get detailed execution status."""
        result = await self.db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.id == execution_id,
                WorkflowExecution.tenant_id == self.tenant_id,
            )
        )
        execution = result.scalar_one_or_none()
        if not execution:
            raise ValueError(f"Workflow execution {execution_id} not found")

        # Get step executions
        step_result = await self.db.execute(
            select(WorkflowStepExecution)
            .where(WorkflowStepExecution.workflow_execution_id == execution_id)
            .order_by(WorkflowStepExecution.started_at)
        )
        steps = step_result.scalars().all()

        return {
            "execution_id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "status": execution.status,
            "current_step": execution.current_step,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_seconds": execution.duration_seconds,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "error_message": execution.error_message,
            "steps": [
                {
                    "step_name": step.step_name,
                    "step_type": step.step_type,
                    "status": step.status,
                    "duration_seconds": step.duration_seconds,
                    "error_message": step.error_message,
                    "retry_count": step.retry_count,
                }
                for step in steps
            ],
        }
