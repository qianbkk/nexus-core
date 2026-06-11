"""
Database Models - Iteration 1: User, Note, Workflow Core Entities
Production-ready SQLAlchemy async models with full audit trail
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

Base = declarative_base()


class User(Base):
    """User model with security features"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Security fields
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Account protection
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_users_email_active', 'email', 'is_active'),
    )


class RefreshToken(Base):
    """Refresh token management for secure session handling"""
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)
    
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    # Device info for security tracking
    device_info = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    user = relationship("User", back_populates="refresh_tokens")


class Note(Base):
    """Note model with versioning and knowledge graph support"""
    __tablename__ = "notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)  # Rendered HTML
    
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Organization
    notebook_id = Column(UUID(as_uuid=True), ForeignKey("notebooks.id", ondelete="SET NULL"), nullable=True)
    tags = Column(ARRAY(String), default=list)
    
    # Knowledge graph
    linked_note_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    
    # Versioning
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="notes")
    versions = relationship("NoteVersion", back_populates="note", cascade="all, delete-orphan")
    comments = relationship("NoteComment", back_populates="note", cascade="all, delete-orphan")
    notebook = relationship("Notebook", back_populates="notes")
    
    __table_args__ = (
        Index('idx_notes_owner_deleted', 'owner_id', 'is_deleted'),
        Index('idx_notes_tags', 'tags', postgresql_using='gin'),
    )


class NoteVersion(Base):
    """Note version history for audit and recovery"""
    __tablename__ = "note_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    content = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)
    title = Column(String(500), nullable=False)
    
    # Metadata
    change_summary = Column(String(1000), nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    note = relationship("Note", back_populates="versions")


class Notebook(Base):
    """Notebook for organizing notes"""
    __tablename__ = "notebooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=True)
    
    color = Column(String(7), default="#3B82F6")  # Hex color
    icon = Column(String(50), default="folder")
    
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    notes = relationship("Note", back_populates="notebook")
    parent = relationship("Notebook", remote_side=[id], backref="children")


class NoteComment(Base):
    """Comments on notes for collaboration"""
    __tablename__ = "note_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    content = Column(Text, nullable=False)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("note_comments.id", ondelete="CASCADE"), nullable=True)
    
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    note = relationship("Note", back_populates="comments")
    parent = relationship("NoteComment", remote_side=[id], backref="replies")


class Workflow(Base):
    """Workflow definition for automation"""
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Workflow definition
    trigger_type = Column(String(50), nullable=False)  # manual, scheduled, webhook, event
    trigger_config = Column(JSON, nullable=True)
    
    steps = Column(JSON, nullable=False)  # List of workflow steps
    is_active = Column(Boolean, default=True)
    
    # Execution settings
    max_retries = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=300)
    
    # Statistics
    execution_count = Column(Integer, default=0)
    last_execution_at = Column(DateTime, nullable=True)
    last_execution_status = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    webhooks = relationship("WorkflowWebhook", back_populates="workflow", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_workflows_owner_active', 'owner_id', 'is_active'),
    )


class WorkflowExecution(Base):
    """Workflow execution history and state"""
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(String(20), default="pending")  # pending, running, success, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Execution context
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Step-by-step progress
    current_step = Column(Integer, default=0)
    step_results = Column(JSON, default=list)
    
    retry_count = Column(Integer, default=0)
    
    workflow = relationship("Workflow", back_populates="executions")


class WorkflowWebhook(Base):
    """Webhook endpoints for workflow triggers"""
    __tablename__ = "workflow_webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    
    webhook_url = Column(String(500), unique=True, nullable=False)
    secret_token = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    workflow = relationship("Workflow", back_populates="webhooks")


class AuditLog(Base):
    """Immutable audit log for compliance and security"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String(50), nullable=False)  # USER, NOTE, WORKFLOW, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    
    # Data
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid conflict
    
    # Status
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
    )
