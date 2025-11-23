"""Add performance indexes for query optimization

Revision ID: add_performance_indexes
Revises: ecc4af4f162e
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_performance_indexes'
down_revision: Union[str, None] = 'ecc4af4f162e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes."""

    # Users table indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('idx_users_tenant_status', 'users', ['tenant_id', 'status'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])

    # Tenants table indexes
    op.create_index('idx_tenants_slug', 'tenants', ['slug'], unique=True)
    op.create_index('idx_tenants_status', 'tenants', ['status'])

    # Agents table indexes
    op.create_index('idx_agents_tenant_id', 'agents', ['tenant_id'])
    op.create_index('idx_agents_slug', 'agents', ['slug'])
    op.create_index('idx_agents_tenant_slug', 'agents', ['tenant_id', 'slug'], unique=True)
    op.create_index('idx_agents_status', 'agents', ['status'])
    op.create_index('idx_agents_created_at', 'agents', ['created_at'])
    op.create_index('idx_agents_deleted_at', 'agents', ['deleted_at'])

    # Conversations table indexes
    op.create_index('idx_conversations_tenant_id', 'conversations', ['tenant_id'])
    op.create_index('idx_conversations_agent_id', 'conversations', ['agent_id'])
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])
    op.create_index('idx_conversations_tenant_created', 'conversations', ['tenant_id', 'created_at'])

    # Messages table indexes
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_messages_conv_created', 'messages', ['conversation_id', 'created_at'])

    # Collections table indexes
    op.create_index('idx_collections_tenant_id', 'collections', ['tenant_id'])
    op.create_index('idx_collections_slug', 'collections', ['slug'])
    op.create_index('idx_collections_tenant_slug', 'collections', ['tenant_id', 'slug'], unique=True)
    op.create_index('idx_collections_created_at', 'collections', ['created_at'])
    op.create_index('idx_collections_deleted_at', 'collections', ['deleted_at'])

    # Documents table indexes
    op.create_index('idx_documents_tenant_id', 'documents', ['tenant_id'])
    op.create_index('idx_documents_collection_id', 'documents', ['collection_id'])
    op.create_index('idx_documents_status', 'documents', ['status'])
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])
    op.create_index('idx_documents_collection_status', 'documents', ['collection_id', 'status'])

    # Document chunks table indexes
    op.create_index('idx_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_chunks_collection_id', 'document_chunks', ['collection_id'])
    op.create_index('idx_chunks_chunk_index', 'document_chunks', ['chunk_index'])

    # Vector index for semantic search (using HNSW for better performance)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    # MCP Servers table indexes
    op.create_index('idx_mcp_servers_tenant_id', 'mcp_servers', ['tenant_id'])
    op.create_index('idx_mcp_servers_slug', 'mcp_servers', ['slug'])
    op.create_index('idx_mcp_servers_status', 'mcp_servers', ['status'])
    op.create_index('idx_mcp_servers_tenant_status', 'mcp_servers', ['tenant_id', 'status'])

    # MCP Server Configs table indexes
    op.create_index('idx_mcp_configs_server_id', 'mcp_server_configs', ['server_id'])
    op.create_index('idx_mcp_configs_agent_id', 'mcp_server_configs', ['agent_id'])

    # Workflows table indexes
    op.create_index('idx_workflows_tenant_id', 'workflows', ['tenant_id'])
    op.create_index('idx_workflows_slug', 'workflows', ['slug'])
    op.create_index('idx_workflows_status', 'workflows', ['status'])
    op.create_index('idx_workflows_tenant_slug', 'workflows', ['tenant_id', 'slug'], unique=True)
    op.create_index('idx_workflows_created_at', 'workflows', ['created_at'])
    op.create_index('idx_workflows_deleted_at', 'workflows', ['deleted_at'])

    # Workflow Executions table indexes
    op.create_index('idx_executions_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('idx_executions_tenant_id', 'workflow_executions', ['tenant_id'])
    op.create_index('idx_executions_status', 'workflow_executions', ['status'])
    op.create_index('idx_executions_started_at', 'workflow_executions', ['started_at'])
    op.create_index('idx_executions_workflow_started', 'workflow_executions', ['workflow_id', 'started_at'])
    op.create_index('idx_executions_tenant_status', 'workflow_executions', ['tenant_id', 'status'])


def downgrade() -> None:
    """Remove performance indexes."""

    # Workflow Executions indexes
    op.drop_index('idx_executions_tenant_status', table_name='workflow_executions')
    op.drop_index('idx_executions_workflow_started', table_name='workflow_executions')
    op.drop_index('idx_executions_started_at', table_name='workflow_executions')
    op.drop_index('idx_executions_status', table_name='workflow_executions')
    op.drop_index('idx_executions_tenant_id', table_name='workflow_executions')
    op.drop_index('idx_executions_workflow_id', table_name='workflow_executions')

    # Workflows indexes
    op.drop_index('idx_workflows_deleted_at', table_name='workflows')
    op.drop_index('idx_workflows_created_at', table_name='workflows')
    op.drop_index('idx_workflows_tenant_slug', table_name='workflows')
    op.drop_index('idx_workflows_status', table_name='workflows')
    op.drop_index('idx_workflows_slug', table_name='workflows')
    op.drop_index('idx_workflows_tenant_id', table_name='workflows')

    # MCP Server Configs indexes
    op.drop_index('idx_mcp_configs_agent_id', table_name='mcp_server_configs')
    op.drop_index('idx_mcp_configs_server_id', table_name='mcp_server_configs')

    # MCP Servers indexes
    op.drop_index('idx_mcp_servers_tenant_status', table_name='mcp_servers')
    op.drop_index('idx_mcp_servers_status', table_name='mcp_servers')
    op.drop_index('idx_mcp_servers_slug', table_name='mcp_servers')
    op.drop_index('idx_mcp_servers_tenant_id', table_name='mcp_servers')

    # Vector index
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw;")

    # Document chunks indexes
    op.drop_index('idx_chunks_chunk_index', table_name='document_chunks')
    op.drop_index('idx_chunks_collection_id', table_name='document_chunks')
    op.drop_index('idx_chunks_document_id', table_name='document_chunks')

    # Documents indexes
    op.drop_index('idx_documents_collection_status', table_name='documents')
    op.drop_index('idx_documents_created_at', table_name='documents')
    op.drop_index('idx_documents_status', table_name='documents')
    op.drop_index('idx_documents_collection_id', table_name='documents')
    op.drop_index('idx_documents_tenant_id', table_name='documents')

    # Collections indexes
    op.drop_index('idx_collections_deleted_at', table_name='collections')
    op.drop_index('idx_collections_created_at', table_name='collections')
    op.drop_index('idx_collections_tenant_slug', table_name='collections')
    op.drop_index('idx_collections_slug', table_name='collections')
    op.drop_index('idx_collections_tenant_id', table_name='collections')

    # Messages indexes
    op.drop_index('idx_messages_conv_created', table_name='messages')
    op.drop_index('idx_messages_created_at', table_name='messages')
    op.drop_index('idx_messages_conversation_id', table_name='messages')

    # Conversations indexes
    op.drop_index('idx_conversations_tenant_created', table_name='conversations')
    op.drop_index('idx_conversations_created_at', table_name='conversations')
    op.drop_index('idx_conversations_user_id', table_name='conversations')
    op.drop_index('idx_conversations_agent_id', table_name='conversations')
    op.drop_index('idx_conversations_tenant_id', table_name='conversations')

    # Agents indexes
    op.drop_index('idx_agents_deleted_at', table_name='agents')
    op.drop_index('idx_agents_created_at', table_name='agents')
    op.drop_index('idx_agents_status', table_name='agents')
    op.drop_index('idx_agents_tenant_slug', table_name='agents')
    op.drop_index('idx_agents_slug', table_name='agents')
    op.drop_index('idx_agents_tenant_id', table_name='agents')

    # Tenants indexes
    op.drop_index('idx_tenants_status', table_name='tenants')
    op.drop_index('idx_tenants_slug', table_name='tenants')

    # Users indexes
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_tenant_status', table_name='users')
    op.drop_index('idx_users_tenant_id', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
