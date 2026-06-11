"""Initial migration - Create all Nexus Core tables

Revision ID: 2579b5aa1cd3
Revises: 
Create Date: 2026-06-11 20:31:53.975383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON


# revision identifiers, used by Alembic.
revision: str = '2579b5aa1cd3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create all Nexus Core tables."""
    
    # Users table
    op.create_table('users',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('login_attempts', sa.Integer(), nullable=True, default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=True, default=False),
        sa.Column('mfa_secret', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'])
    
    # Refresh tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=True, default=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('device_info', JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_refresh_tokens_token', 'refresh_tokens', ['token_hash'], unique=True)
    
    # Notebooks table
    op.create_table('notebooks',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', UUID(as_uuid=True), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True, default='#3B82F6'),
        sa.Column('icon', sa.String(length=50), nullable=True, default='folder'),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['notebooks.id'], ondelete='CASCADE')
    )
    
    # Notes table
    op.create_table('notes',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('owner_id', UUID(as_uuid=True), nullable=False),
        sa.Column('notebook_id', UUID(as_uuid=True), nullable=True),
        sa.Column('tags', ARRAY(sa.String()), nullable=True, default=list),
        sa.Column('linked_note_ids', ARRAY(UUID(as_uuid=True)), nullable=True, default=list),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['notebook_id'], ['notebooks.id'], ondelete='SET NULL')
    )
    op.create_index('idx_notes_owner_deleted', 'notes', ['owner_id', 'is_deleted'])
    
    # Note versions table
    op.create_table('note_versions',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('note_id', UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('change_summary', sa.String(length=1000), nullable=True),
        sa.Column('author_id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'])
    )
    
    # Note comments table
    op.create_table('note_comments',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('note_id', UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', UUID(as_uuid=True), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['note_comments.id'], ondelete='CASCADE')
    )
    
    # Workflows table
    op.create_table('workflows',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('trigger_config', JSON(), nullable=True),
        sa.Column('steps', JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('max_retries', sa.Integer(), nullable=True, default=3),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True, default=300),
        sa.Column('execution_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_execution_at', sa.DateTime(), nullable=True),
        sa.Column('last_execution_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.utcnow(), onupdate=sa.func.utcnow()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_workflows_owner_active', 'workflows', ['owner_id', 'is_active'])
    
    # Workflow executions table
    op.create_table('workflow_executions',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('input_data', JSON(), nullable=True),
        sa.Column('output_data', JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('current_step', sa.Integer(), nullable=True, default=0),
        sa.Column('step_results', JSON(), nullable=True, default=list),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE')
    )
    
    # Workflow webhooks table
    op.create_table('workflow_webhooks',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', UUID(as_uuid=True), nullable=False),
        sa.Column('webhook_url', sa.String(length=500), nullable=False),
        sa.Column('secret_token', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('webhook_url')
    )
    
    # Audit logs table
    op.create_table('audit_logs',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('request_method', sa.String(length=10), nullable=True),
        sa.Column('request_path', sa.String(length=500), nullable=True),
        sa.Column('old_values', JSON(), nullable=True),
        sa.Column('new_values', JSON(), nullable=True),
        sa.Column('extra_metadata', JSON(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True, default=sa.func.utcnow()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])


def downgrade() -> None:
    """Downgrade schema - Drop all Nexus Core tables."""
    op.drop_table('audit_logs')
    op.drop_table('workflow_webhooks')
    op.drop_table('workflow_executions')
    op.drop_table('workflows')
    op.drop_table('note_comments')
    op.drop_table('note_versions')
    op.drop_table('notes')
    op.drop_table('notebooks')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
