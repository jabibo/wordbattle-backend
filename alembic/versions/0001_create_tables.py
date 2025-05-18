"""create tables

Revision ID: 0001
Revises: 
Create Date: 2025-05-18 00:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('username', sa.String, unique=True, index=True),
        sa.Column('hashed_password', sa.String)
    )

    op.create_table('games',
        sa.Column('id', sa.String, primary_key=True, index=True),
        sa.Column('state', sa.Text),
        sa.Column('current_player_id', sa.Integer, sa.ForeignKey('users.id'))
    )

    op.create_table('moves',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('game_id', sa.String, sa.ForeignKey('games.id')),
        sa.Column('player_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('move_data', sa.Text),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('moves')
    op.drop_table('games')
    op.drop_table('users')
