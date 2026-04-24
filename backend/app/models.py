"""
SQLAlchemy ORM Models for NexusAI.
Defines all database tables and relationships.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Enum,
    UniqueConstraint, Index, TIMESTAMP, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from backend.app.core.database import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    organizations = relationship("Organization", back_populates="owner", foreign_keys="Organization.owner_id")
    organization_members = relationship("OrganizationMember", back_populates="user")
    projects = relationship("Project", back_populates="created_by_user")
    project_members = relationship("ProjectMember", back_populates="user")
    files = relationship("ProjectFile", back_populates="created_by_user")
    file_versions = relationship("FileVersion", back_populates="created_by_user")
    sessions = relationship("Session", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('username', name='uq_user_username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_is_active', 'is_active'),
    )


class Organization(Base):
    """Organization/Team model."""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    settings = Column(JSON, default={}, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="organizations", foreign_keys=[owner_id])
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    """Organization membership with roles."""
    __tablename__ = "organization_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member", nullable=False)  # owner, admin, member, viewer
    joined_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_members")

    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_org_user'),
        Index('idx_organization_id', 'organization_id'),
        Index('idx_user_id', 'user_id'),
    )


class Project(Base):
    """Project/Workspace model."""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    git_url = Column(String(500), nullable=True)
    git_branch = Column(String(255), default="main", nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    settings = Column(JSON, default={}, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    created_by_user = relationship("User", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    executions = relationship("CodeExecution", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_organization_id', 'organization_id'),
        Index('idx_created_by_id', 'created_by_id'),
    )


class ProjectMember(Base):
    """Project membership with roles."""
    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="editor", nullable=False)  # owner, editor, viewer
    joined_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_members")

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
        Index('idx_project_id', 'project_id'),
        Index('idx_user_id', 'user_id'),
    )


class ProjectFile(Base):
    """File in a project."""
    __tablename__ = "project_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    path = Column(String(500), nullable=False)  # relative path like "src/main.py"
    content = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)  # python, javascript, etc.
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="files")
    created_by_user = relationship("User", back_populates="files")
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('project_id', 'path', name='uq_project_path'),
        Index('idx_project_id', 'project_id'),
        Index('idx_path', 'path'),
    )


class FileVersion(Base):
    """Version history for files."""
    __tablename__ = "file_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("project_files.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    commit_message = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    file = relationship("ProjectFile", back_populates="versions")
    created_by_user = relationship("User", back_populates="file_versions")

    __table_args__ = (
        Index('idx_file_id', 'file_id'),
        Index('idx_created_at', 'created_at'),
    )


class Session(Base):
    """User session state (chat history, code context, etc.)."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    code_context = Column(JSON, default={}, nullable=False)
    chat_history = Column(JSON, default=[], nullable=False)
    last_execution_error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    project = relationship("Project", back_populates="sessions")

    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_project_id', 'project_id'),
        Index('idx_expires_at', 'expires_at'),
    )


class CodeExecution(Base):
    """Code execution history and results."""
    __tablename__ = "code_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, running, success, error, timeout
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # milliseconds
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="executions")

    __table_args__ = (
        Index('idx_project_id', 'project_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )


class AuditLog(Base):
    """Audit trail for compliance and debugging."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # login, create_file, delete_project, etc.
    resource_type = Column(String(50), nullable=False)  # user, project, file, etc.
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, default={}, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_action', 'action'),
        Index('idx_resource_type', 'resource_type'),
        Index('idx_created_at', 'created_at'),
    )


class Secret(Base):
    """Encrypted secrets storage (API keys, tokens, etc.)."""
    __tablename__ = "secrets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    encrypted_value = Column(Text, nullable=False)
    secret_type = Column(String(50), nullable=False)  # api_key, github_token, ssh_key, etc.
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_secret_name'),
        Index('idx_user_id', 'user_id'),
    )
