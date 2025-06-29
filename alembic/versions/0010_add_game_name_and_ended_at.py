"""Add name and ended_at fields to Game model for contract compliance

Revision ID: 0010_add_game_name_and_ended_at
Revises: 63f920666b37
Create Date: 2024-12-18 14:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010_add_game_name_and_ended_at'
down_revision = '63f920666b37'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add name field to games table for contract compliance
    op.add_column('games', sa.Column('name', sa.String(), nullable=True))
    
    # Add ended_at field to games table for forfeit tracking
    op.add_column('games', sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('games', 'ended_at')
    op.drop_column('games', 'name') 