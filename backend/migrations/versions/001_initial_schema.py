"""
Initial database migration - Create all tables.

Revision ID: 001_initial_schema
Create Date: 2024-04-23 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superadmin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_user_email'),
        sa.UniqueConstraint('username', name='uq_user_username'),
    )
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_is_active', 'users', ['is_active'])

    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('settings', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create organization_members table
    op.create_table(
        'organization_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_user'),
    )
    op.create_index('idx_organization_id', 'organization_members', ['organization_id'])
    op.create_index('idx_user_id', 'organization_members', ['user_id'])

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('git_url', sa.String(500), nullable=True),
        sa.Column('git_branch', sa.String(255), nullable=False, server_default='main'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('settings', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_organization_id_projects', 'projects', ['organization_id'])
    op.create_index('idx_created_by_id', 'projects', ['created_by_id'])

    # Create project_members table
    op.create_table(
        'project_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='editor'),
        sa.Column('joined_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
    )
    op.create_index('idx_project_id_members', 'project_members', ['project_id'])
    op.create_index('idx_user_id_members', 'project_members', ['user_id'])

    # Create project_files table
    op.create_table(
        'project_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('language', sa.String(50), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'path', name='uq_project_path'),
    )
    op.create_index('idx_project_id_files', 'project_files', ['project_id'])
    op.create_index('idx_path', 'project_files', ['path'])

    # Create file_versions table
    op.create_table(
        'file_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('commit_message', sa.String(500), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['file_id'], ['project_files.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_file_id', 'file_versions', ['file_id'])
    op.create_index('idx_created_at', 'file_versions', ['created_at'])

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code_context', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('chat_history', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('last_execution_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_user_id_sessions', 'sessions', ['user_id'])
    op.create_index('idx_project_id_sessions', 'sessions', ['project_id'])
    op.create_index('idx_expires_at', 'sessions', ['expires_at'])

    # Create code_executions table
    op.create_table(
        'code_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('language', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('execution_time', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_project_id_exec', 'code_executions', ['project_id'])
    op.create_index('idx_status', 'code_executions', ['status'])
    op.create_index('idx_created_at_exec', 'code_executions', ['created_at'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('details', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_user_id_audit', 'audit_logs', ['user_id'])
    op.create_index('idx_action', 'audit_logs', ['action'])
    op.create_index('idx_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('idx_created_at_audit', 'audit_logs', ['created_at'])

    # Create secrets table
    op.create_table(
        'secrets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('secret_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_secret_name'),
    )
    op.create_index('idx_user_id_secrets', 'secrets', ['user_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_user_id_secrets', table_name='secrets')
    op.drop_table('secrets')
    op.drop_index('idx_created_at_audit', table_name='audit_logs')
    op.drop_index('idx_resource_type', table_name='audit_logs')
    op.drop_index('idx_action', table_name='audit_logs')
    op.drop_index('idx_user_id_audit', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('idx_created_at_exec', table_name='code_executions')
    op.drop_index('idx_status', table_name='code_executions')
    op.drop_index('idx_project_id_exec', table_name='code_executions')
    op.drop_table('code_executions')
    op.drop_index('idx_expires_at', table_name='sessions')
    op.drop_index('idx_project_id_sessions', table_name='sessions')
    op.drop_index('idx_user_id_sessions', table_name='sessions')
    op.drop_table('sessions')
    op.drop_index('idx_created_at', table_name='file_versions')
    op.drop_index('idx_file_id', table_name='file_versions')
    op.drop_table('file_versions')
    op.drop_index('idx_path', table_name='project_files')
    op.drop_index('idx_project_id_files', table_name='project_files')
    op.drop_table('project_files')
    op.drop_index('idx_user_id_members', table_name='project_members')
    op.drop_index('idx_project_id_members', table_name='project_members')
    op.drop_table('project_members')
    op.drop_index('idx_created_by_id', table_name='projects')
    op.drop_index('idx_organization_id_projects', table_name='projects')
    op.drop_table('projects')
    op.drop_index('idx_user_id', table_name='organization_members')
    op.drop_index('idx_organization_id', table_name='organization_members')
    op.drop_table('organization_members')
    op.drop_table('organizations')
    op.drop_index('idx_user_is_active', table_name='users')
    op.drop_index('idx_user_email', table_name='users')
    op.drop_table('users')
