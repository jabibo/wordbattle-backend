"""add players table

Revision ID: 0002b
Revises: 0001
Create Date: 2025-05-18 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '0002b'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'players',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('game_id', sa.String, sa.ForeignKey('games.id')),
        sa.Column('rack', sa.String),
        sa.Column('score', sa.Integer, default=0)
    )

def downgrade():
    op.drop_table('players')
