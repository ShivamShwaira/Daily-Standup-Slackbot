"""Initial migration: create base tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create Workspace table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slack_team_id', sa.String(length=255), nullable=False),
        sa.Column('report_channel_id', sa.String(length=255), nullable=False),
        sa.Column('default_time', sa.String(length=10), nullable=False, server_default='09:00'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='America/New_York'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slack_team_id'),
    )

    # Create User table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slack_user_id', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slack_user_id'),
    )

    # Create StandupReport table
    op.create_table(
        'standup_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('feeling', sa.Text(), nullable=True),
        sa.Column('yesterday', sa.Text(), nullable=True),
        sa.Column('today', sa.Text(), nullable=True),
        sa.Column('blockers', sa.Text(), nullable=True),
        sa.Column('skipped', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'report_date'),
    )

    # Create StandupState table
    op.create_table(
        'standup_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('pending_report_date', sa.Date(), nullable=False),
        sa.Column('current_question_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # Create indices for common queries
    op.create_index('ix_users_slack_user_id', 'users', ['slack_user_id'])
    op.create_index('ix_users_active', 'users', ['active'])
    op.create_index('ix_standup_reports_user_id_date', 'standup_reports', ['user_id', 'report_date'])
    op.create_index('ix_standup_states_user_id', 'standup_states', ['user_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_standup_states_user_id')
    op.drop_index('ix_standup_reports_user_id_date')
    op.drop_index('ix_users_active')
    op.drop_index('ix_users_slack_user_id')
    
    op.drop_table('standup_states')
    op.drop_table('standup_reports')
    op.drop_table('users')
    op.drop_table('workspaces')
