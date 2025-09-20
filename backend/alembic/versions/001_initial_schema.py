"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('clerk_user_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('display_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('avatar_url', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_clerk_user_id'), 'users', ['clerk_user_id'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('user_agent', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('ip_address', sqlmodel.sql.sqltypes.AutoString(length=45), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create authproviders table
    op.create_table('authproviders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.Enum('GOOGLE', 'GITHUB', 'LINKEDIN', 'EMAIL', name='authprovidertype'), nullable=False),
        sa.Column('provider_user_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_authproviders_provider'), 'authproviders', ['provider'], unique=False)
    op.create_index(op.f('ix_authproviders_provider_user_id'), 'authproviders', ['provider_user_id'], unique=False)
    op.create_index(op.f('ix_authproviders_user_id'), 'authproviders', ['user_id'], unique=False)

    # Create unique constraint for user_id + provider combination
    op.create_unique_constraint('uq_authproviders_user_provider', 'authproviders', ['user_id', 'provider'])

    # Create unique constraint for provider + provider_user_id combination
    op.create_unique_constraint('uq_authproviders_provider_user', 'authproviders', ['provider', 'provider_user_id'])

    # Create todoitems table
    op.create_table('todoitems',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('session_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=10000), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='todopriority'), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_todoitems_session_id'), 'todoitems', ['session_id'], unique=False)
    op.create_index(op.f('ix_todoitems_user_id'), 'todoitems', ['user_id'], unique=False)

    # Create check constraint to ensure either user_id or session_id is set (but not both)
    op.create_check_constraint(
        'ck_todoitems_user_or_session',
        'todoitems',
        '(user_id IS NOT NULL AND session_id IS NULL) OR (user_id IS NULL AND session_id IS NOT NULL)'
    )


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('todoitems')
    op.drop_table('authproviders')
    op.drop_table('sessions')
    op.drop_table('users')

    # Drop custom enum types
    op.execute('DROP TYPE IF EXISTS authprovidertype')
    op.execute('DROP TYPE IF EXISTS todopriority')