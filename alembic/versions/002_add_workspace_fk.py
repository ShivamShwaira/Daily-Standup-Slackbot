"""Add workspace foreign key to users table

Revision ID: 002_add_workspace_fk
Revises: 001_initial
Create Date: 2025-12-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_workspace_fk'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add workspace_id column to users table
    op.add_column('users', sa.Column('workspace_id', sa.Integer(), nullable=True))
    
    # For existing data, if any, we need to handle it
    # This assumes you have at least one workspace in the database
    # If not, you'll need to create one first or modify this migration
    op.execute('UPDATE users SET workspace_id = 1 WHERE workspace_id IS NULL')
    
    # Now make the column NOT NULL
    op.alter_column('users', 'workspace_id', nullable=False)
    
    # Add the foreign key constraint
    op.create_foreign_key(
        'fk_users_workspace_id',
        'users',
        'workspaces',
        ['workspace_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create index on workspace_id for better query performance
    op.create_index('ix_users_workspace_id', 'users', ['workspace_id'])


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_users_workspace_id')
    
    # Drop the foreign key constraint
    op.drop_constraint('fk_users_workspace_id', 'users', type_='foreignkey')
    
    # Remove the column
    op.drop_column('users', 'workspace_id')
