# Workflow Engine Usage Guide

> **Complete guide to using the Multi-Agent Workflow Engine**
>
> **Version**: 1.0.0
> **Date**: 2025-11-21

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Workflow Concepts](#workflow-concepts)
4. [API Reference](#api-reference)
5. [Step Types](#step-types)
6. [Example Workflows](#example-workflows)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Workflow Engine enables you to:

- **Orchestrate multi-step processes** with sequential or parallel execution
- **Coordinate multiple agents** working together on complex tasks
- **Integrate with MCP tools** for external system access
- **Make HTTP requests** to external APIs
- **Implement conditional logic** and dynamic branching
- **Track execution state** with complete audit trails
- **Handle errors** with automatic retries

### Key Features

- ✅ **Sequential Execution**: Steps run one after another
- ✅ **Parallel Execution**: Multiple steps run simultaneously
- ✅ **Conditional Branching**: Route execution based on results
- ✅ **Agent Integration**: Delegate tasks to specialized agents
- ✅ **MCP Tool Integration**: Execute filesystem, database, and custom tools
- ✅ **HTTP Integration**: Call external APIs
- ✅ **Error Handling**: Automatic retries with exponential backoff
- ✅ **State Management**: Track workflow progress and results
- ✅ **Multi-tenant**: Complete isolation between tenants

---

## Quick Start

### 1. Create a Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/workflows \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Workflow",
    "description": "A simple workflow example",
    "steps": [
      {
        "type": "agent",
        "name": "analyze_data",
        "agent_id": "your-agent-id",
        "input": {
          "instruction": "Analyze this data: {input.data}"
        }
      }
    ]
  }'
```

### 2. Activate the Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/workflows/{workflow_id}/activate \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Execute the Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/workflows/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "{workflow_id}",
    "input_data": {
      "data": "Sample data to analyze"
    }
  }'
```

### 4. Check Execution Status

```bash
curl http://localhost:8000/api/v1/workflows/workflows/executions/{execution_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

## Workflow Concepts

### Workflow Definition

A **workflow** is a reusable template that defines:

- **Steps**: Ordered list of tasks to execute
- **Triggers**: How the workflow is initiated (manual, schedule, webhook)
- **Configuration**: Timeout, retry strategy, etc.
- **Metadata**: Name, description, tags, category

### Workflow Execution

A **workflow execution** is an instance of a workflow being run:

- **Input Data**: Data provided when starting the execution
- **Context**: Accumulates results from each step
- **Status**: pending → running → completed/failed
- **Output Data**: Final results after all steps complete

### Step Types

| Type | Description | Use Case |
|------|-------------|----------|
| **agent** | Delegate task to an AI agent | Analysis, generation, classification |
| **mcp_tool** | Execute an MCP tool | File operations, database queries |
| **parallel** | Run multiple steps simultaneously | Independent research tasks |
| **conditional** | Branch based on conditions | Route by confidence score |
| **http** | Make HTTP request | Call external APIs |

### Template Variables

Use `{variable_name}` syntax to reference data:

```json
{
  "instruction": "Analyze {input.data} and compare with {previous_step.result}"
}
```

Supports nested access: `{step_name.field.subfield}`

---

## API Reference

### Workflows

#### Create Workflow

```http
POST /api/v1/workflows/workflows
```

**Request**:
```json
{
  "name": "Workflow Name",
  "description": "Workflow description",
  "version": "1.0.0",
  "steps": [...],
  "triggers": [...],
  "timeout_seconds": 3600,
  "max_retries": 3,
  "retry_strategy": "exponential",
  "tags": ["tag1", "tag2"],
  "category": "examples"
}
```

**Response**: `WorkflowResponse`

#### List Workflows

```http
GET /api/v1/workflows/workflows?offset=0&limit=50&status=active&category=examples
```

**Response**: `WorkflowListResponse`

#### Get Workflow

```http
GET /api/v1/workflows/workflows/{workflow_id}
```

**Response**: `WorkflowResponse`

#### Update Workflow

```http
PATCH /api/v1/workflows/workflows/{workflow_id}
```

**Request**:
```json
{
  "name": "Updated Name",
  "status": "active"
}
```

**Response**: `WorkflowResponse`

#### Delete Workflow

```http
DELETE /api/v1/workflows/workflows/{workflow_id}
```

**Response**: 204 No Content

#### Activate Workflow

```http
POST /api/v1/workflows/workflows/{workflow_id}/activate
```

**Response**: `WorkflowResponse`

### Executions

#### Execute Workflow

```http
POST /api/v1/workflows/workflows/execute
```

**Request**:
```json
{
  "workflow_id": "uuid",
  "input_data": {
    "key": "value"
  },
  "context": {
    "additional": "context"
  }
}
```

**Response**: `WorkflowExecutionResponse`

#### List Executions

```http
GET /api/v1/workflows/workflows/executions?workflow_id=uuid&status=completed
```

**Response**: `WorkflowExecutionListResponse`

#### Get Execution Details

```http
GET /api/v1/workflows/workflows/executions/{execution_id}
```

**Response**: `WorkflowExecutionDetailResponse` (includes all step executions)

#### Cancel Execution

```http
POST /api/v1/workflows/workflows/executions/{execution_id}/cancel
```

**Response**: `WorkflowExecutionResponse`

#### Get Execution Status

```http
GET /api/v1/workflows/workflows/executions/{execution_id}/status
```

**Response**:
```json
{
  "execution_id": "uuid",
  "status": "running",
  "current_step": "step_name",
  "steps": [...]
}
```

### Tasks

#### Create Agent Task

```http
POST /api/v1/workflows/tasks
```

**Request**:
```json
{
  "agent_id": "uuid",
  "task_type": "execute",
  "instruction": "Task instruction",
  "priority": 5
}
```

**Response**: `AgentTaskResponse`

#### List Tasks

```http
GET /api/v1/workflows/tasks?agent_id=uuid&status=pending
```

**Response**: `AgentTaskListResponse`

#### Get Task

```http
GET /api/v1/workflows/tasks/{task_id}
```

**Response**: `AgentTaskResponse`

#### Update Task

```http
PATCH /api/v1/workflows/tasks/{task_id}
```

**Request**:
```json
{
  "status": "completed",
  "result": {...}
}
```

**Response**: `AgentTaskResponse`

### Messages

#### Create Agent Message

```http
POST /api/v1/workflows/messages
```

**Request**:
```json
{
  "from_agent_id": "uuid",
  "to_agent_id": "uuid",
  "message_type": "request",
  "content": "Message content",
  "requires_response": true
}
```

**Response**: `AgentMessageResponse`

#### List Messages

```http
GET /api/v1/workflows/messages?from_agent_id=uuid&to_agent_id=uuid
```

**Response**: `AgentMessageListResponse`

---

## Step Types

### 1. Agent Step

Execute a task using an AI agent.

**Definition**:
```json
{
  "type": "agent",
  "name": "step_name",
  "agent_id": "uuid",
  "input": {
    "instruction": "Instruction for the agent",
    "context": {}
  },
  "output_mapping": {
    "result_field": "$.response"
  },
  "max_retries": 2,
  "priority": 5
}
```

**Template Variables**:
- Access input: `{input.field_name}`
- Access previous step: `{previous_step.result}`

**Example**:
```json
{
  "type": "agent",
  "name": "analyze_sentiment",
  "agent_id": "sentiment-agent-id",
  "input": {
    "instruction": "Analyze sentiment of: {input.text}",
    "context": {}
  },
  "output_mapping": {
    "sentiment": "$.response.sentiment",
    "confidence": "$.response.confidence"
  }
}
```

### 2. MCP Tool Step

Execute an MCP tool.

**Definition**:
```json
{
  "type": "mcp_tool",
  "name": "step_name",
  "server_id": "mcp-server-uuid",
  "tool_name": "tool_name",
  "input": {
    "arg1": "value1",
    "arg2": "{input.field}"
  }
}
```

**Example**:
```json
{
  "type": "mcp_tool",
  "name": "save_result",
  "server_id": "filesystem-server-id",
  "tool_name": "write_file",
  "input": {
    "path": "/tmp/result.txt",
    "content": "{analyze_sentiment.response}"
  }
}
```

### 3. Parallel Step

Execute multiple steps simultaneously.

**Definition**:
```json
{
  "type": "parallel",
  "name": "step_name",
  "steps": [
    { "type": "agent", ... },
    { "type": "agent", ... }
  ],
  "wait_for": "all"  // Options: all, any, count:N
}
```

**Wait Strategies**:
- `all`: Wait for all steps to complete
- `any`: Wait for any one step to complete
- `count:N`: Wait for N steps to complete

**Example**:
```json
{
  "type": "parallel",
  "name": "parallel_research",
  "steps": [
    {
      "type": "agent",
      "name": "research_a",
      "agent_id": "agent-1-id",
      "input": {
        "instruction": "Research topic A"
      }
    },
    {
      "type": "agent",
      "name": "research_b",
      "agent_id": "agent-2-id",
      "input": {
        "instruction": "Research topic B"
      }
    }
  ],
  "wait_for": "all"
}
```

### 4. Conditional Step

Branch execution based on conditions.

**Definition**:
```json
{
  "type": "conditional",
  "name": "step_name",
  "condition": "$.previous_step.field > 0.8",
  "if_true": { "type": "agent", ... },
  "if_false": { "type": "agent", ... }
}
```

**Condition Syntax**:
- JSONPath-like: `$.step_name.field`
- Operators: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Values: numbers, strings (quoted), `true`, `false`, `null`

**Example**:
```json
{
  "type": "conditional",
  "name": "check_confidence",
  "condition": "$.analyze_sentiment.confidence > 0.8",
  "if_true": {
    "type": "agent",
    "name": "high_confidence_action",
    "agent_id": "agent-id",
    "input": {
      "instruction": "Process high confidence result"
    }
  },
  "if_false": {
    "type": "agent",
    "name": "low_confidence_action",
    "agent_id": "agent-id",
    "input": {
      "instruction": "Request manual review"
    }
  }
}
```

### 5. HTTP Step

Make an HTTP request.

**Definition**:
```json
{
  "type": "http",
  "name": "step_name",
  "method": "POST",
  "url": "https://api.example.com/endpoint",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer {input.api_key}"
  },
  "body": {
    "data": "{previous_step.result}"
  }
}
```

**Methods**: GET, POST, PUT, PATCH, DELETE

**Response**:
```json
{
  "status": 200,
  "headers": {},
  "body": {}
}
```

**Example**:
```json
{
  "type": "http",
  "name": "notify_webhook",
  "method": "POST",
  "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "text": "Workflow completed: {input.workflow_name}"
  }
}
```

---

## Example Workflows

### Example 1: Simple Sequential Analysis

```json
{
  "name": "Simple Sequential Analysis",
  "description": "Analyze data and generate summary",
  "steps": [
    {
      "type": "agent",
      "name": "initial_analysis",
      "agent_id": "analyzer-agent-id",
      "input": {
        "instruction": "Analyze: {input.data}"
      },
      "output_mapping": {
        "analysis": "$.response"
      }
    },
    {
      "type": "agent",
      "name": "generate_summary",
      "agent_id": "summarizer-agent-id",
      "input": {
        "instruction": "Summarize: {initial_analysis.analysis}"
      }
    }
  ]
}
```

### Example 2: Parallel Research Workflow

```json
{
  "name": "Parallel Research",
  "description": "Research multiple topics and synthesize",
  "steps": [
    {
      "type": "parallel",
      "name": "research_topics",
      "steps": [
        {
          "type": "agent",
          "name": "topic_a",
          "agent_id": "researcher-id",
          "input": {
            "instruction": "Research: {input.topic_a}"
          }
        },
        {
          "type": "agent",
          "name": "topic_b",
          "agent_id": "researcher-id",
          "input": {
            "instruction": "Research: {input.topic_b}"
          }
        }
      ],
      "wait_for": "all"
    },
    {
      "type": "agent",
      "name": "synthesize",
      "agent_id": "synthesizer-id",
      "input": {
        "instruction": "Synthesize research",
        "context": {
          "research_a": "{research_topics.step_0}",
          "research_b": "{research_topics.step_1}"
        }
      }
    }
  ]
}
```

### Example 3: Conditional Routing

```json
{
  "name": "Conditional Processing",
  "description": "Route based on classification confidence",
  "steps": [
    {
      "type": "agent",
      "name": "classify",
      "agent_id": "classifier-id",
      "input": {
        "instruction": "Classify and provide confidence: {input.request}"
      },
      "output_mapping": {
        "confidence": "$.confidence",
        "category": "$.category"
      }
    },
    {
      "type": "conditional",
      "name": "route",
      "condition": "$.classify.confidence > 0.8",
      "if_true": {
        "type": "agent",
        "name": "auto_process",
        "agent_id": "processor-id",
        "input": {
          "instruction": "Automatically process: {input.request}"
        }
      },
      "if_false": {
        "type": "agent",
        "name": "manual_review",
        "agent_id": "reviewer-id",
        "input": {
          "instruction": "Queue for manual review: {input.request}"
        }
      }
    }
  ]
}
```

### Example 4: ETL Pipeline

```json
{
  "name": "Data ETL Pipeline",
  "description": "Extract, transform, validate, and load data",
  "steps": [
    {
      "type": "agent",
      "name": "extract",
      "agent_id": "extractor-id",
      "input": {
        "instruction": "Extract from: {input.source}"
      }
    },
    {
      "type": "agent",
      "name": "transform",
      "agent_id": "transformer-id",
      "input": {
        "instruction": "Transform data",
        "context": {
          "data": "{extract.response}"
        }
      }
    },
    {
      "type": "agent",
      "name": "validate",
      "agent_id": "validator-id",
      "input": {
        "instruction": "Validate data",
        "context": {
          "data": "{transform.response}"
        }
      },
      "output_mapping": {
        "is_valid": "$.is_valid"
      }
    },
    {
      "type": "conditional",
      "name": "check_validation",
      "condition": "$.validate.is_valid == true",
      "if_true": {
        "type": "mcp_tool",
        "name": "load",
        "server_id": "database-server-id",
        "tool_name": "insert",
        "input": {
          "data": "{transform.response}"
        }
      },
      "if_false": {
        "type": "agent",
        "name": "handle_error",
        "agent_id": "error-handler-id",
        "input": {
          "instruction": "Handle validation failure"
        }
      }
    }
  ]
}
```

---

## Best Practices

### Workflow Design

1. **Keep Steps Focused**: Each step should have a single, clear purpose
2. **Use Descriptive Names**: Name steps clearly (e.g., `validate_input`, not `step1`)
3. **Plan for Failures**: Use retry strategies and error handling
4. **Minimize Dependencies**: Use parallel steps when tasks are independent
5. **Document Context**: Use meaningful field names in output mappings

### Performance Optimization

1. **Parallel When Possible**: Use parallel steps for independent tasks
2. **Set Appropriate Timeouts**: Don't make them too long or too short
3. **Use Conditional Branches**: Skip unnecessary steps
4. **Cache Results**: Store intermediate results for reuse
5. **Monitor Execution**: Track duration and optimize slow steps

### Error Handling

1. **Set Max Retries**: 2-3 retries with exponential backoff
2. **Handle Edge Cases**: Use conditionals to check for errors
3. **Graceful Degradation**: Provide fallback steps
4. **Log Errors**: All errors are logged automatically
5. **Test Failure Scenarios**: Test your workflows with invalid inputs

### Security

1. **Validate Inputs**: Always validate workflow input data
2. **Sanitize Variables**: Be careful with user-provided data in templates
3. **Limit Tool Access**: Only grant necessary permissions to MCP tools
4. **Encrypt Sensitive Data**: Don't store credentials in workflow definitions
5. **Audit Executions**: Review execution logs regularly

---

## Troubleshooting

### Common Issues

#### Workflow Execution Fails Immediately

**Problem**: Workflow status is `failed` with no steps executed

**Possible Causes**:
- Workflow not in `active` status
- Invalid workflow definition
- Missing required input data

**Solution**:
1. Check workflow status: `GET /workflows/{id}`
2. Activate if needed: `POST /workflows/{id}/activate`
3. Validate step definitions
4. Ensure input_data contains all required fields

#### Step Execution Hangs

**Problem**: Step status stuck in `running`

**Possible Causes**:
- Agent timeout
- MCP server not responding
- HTTP request timeout

**Solution**:
1. Check execution status: `GET /executions/{id}/status`
2. Cancel if needed: `POST /executions/{id}/cancel`
3. Increase workflow `timeout_seconds`
4. Check agent and MCP server health

#### Template Variables Not Resolving

**Problem**: Variables like `{input.field}` appear literally in results

**Possible Causes**:
- Incorrect variable syntax
- Referenced field doesn't exist
- Typo in field name

**Solution**:
1. Check variable syntax: `{step_name.field}`
2. Verify field exists in context
3. Use execution detail response to see available fields
4. Check for typos

#### Conditional Not Working

**Problem**: Wrong branch is executed

**Possible Causes**:
- Incorrect condition syntax
- Wrong operator
- Type mismatch (string vs number)

**Solution**:
1. Check condition format: `$.step.field > value`
2. Verify operator: `>`, `<`, `>=`, `<=`, `==`, `!=`
3. Check value types (use quotes for strings)
4. Review step execution output

### Debug Workflow Execution

1. **Get Detailed Status**:
```bash
curl http://localhost:8000/api/v1/workflows/workflows/executions/{id}/status \
  -H "Authorization: Bearer $TOKEN"
```

2. **Check Step-by-Step**:
```bash
curl http://localhost:8000/api/v1/workflows/workflows/executions/{id} \
  -H "Authorization: Bearer $TOKEN"
```

3. **Review Step Output**:
```json
{
  "steps": [
    {
      "step_name": "analyze",
      "status": "completed",
      "output_data": {...},
      "error_message": null
    }
  ]
}
```

4. **Check Logs**: Look at step `error_message` fields

### Performance Issues

#### Slow Execution

**Symptoms**: Workflow takes longer than expected

**Solutions**:
1. Use parallel steps for independent tasks
2. Optimize agent prompts (be specific and concise)
3. Reduce unnecessary steps
4. Check agent and MCP server performance
5. Monitor step `duration_seconds`

#### High Resource Usage

**Symptoms**: System slow during workflow execution

**Solutions**:
1. Limit parallel step count
2. Reduce workflow concurrency
3. Optimize agent model selection
4. Use smaller context in agent steps
5. Clean up old executions

---

## Additional Resources

- **Architecture**: `docs/WORKFLOW_ARCHITECTURE.md`
- **API Documentation**: http://localhost:8000/docs
- **Example Templates**: Query workflows with `category=examples`
- **Session Summary**: `docs/SESSION_SUMMARY_2025-11-21.md`

---

## Support

For issues and questions:

1. Check this documentation
2. Review example workflows
3. Check execution status and error messages
4. Review the architecture document

---

*Last Updated: 2025-11-21*
*Version: 1.0.0*
