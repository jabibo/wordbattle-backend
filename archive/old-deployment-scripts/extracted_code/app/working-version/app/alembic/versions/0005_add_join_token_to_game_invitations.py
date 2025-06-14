"""Add join_token to game_invitations

Revision ID: 0005
Revises: 0004
Create Date: 2025-05-28 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    # Add join_token column to game_invitations table
    op.add_column('game_invitations', sa.Column('join_token', sa.String(), nullable=True))
    
    # Create unique constraint on join_token
    op.create_unique_constraint('uq_game_invitations_join_token', 'game_invitations', ['join_token'])
    
    # Create index for faster lookups
    op.create_index('ix_game_invitations_join_token', 'game_invitations', ['join_token'])


def downgrade():
    # Remove index
    op.drop_index('ix_game_invitations_join_token', table_name='game_invitations')
    
    # Remove unique constraint
    op.drop_constraint('uq_game_invitations_join_token', 'game_invitations', type_='unique')
    
    # Remove column
    op.drop_column('game_invitations', 'join_token') 