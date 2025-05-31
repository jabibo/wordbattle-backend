"""add game columns

Revision ID: 0003
Revises: 0002b
Create Date: 2024-03-19 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from app.models.game import GameStatus

revision = '0003'
down_revision = '0002b'
branch_labels = None
depends_on = None

def upgrade():
    # Create GameStatus enum type
    op.execute("CREATE TYPE gamestatus AS ENUM ('setup', 'ready', 'in_progress', 'completed', 'cancelled')")
    
    # Add new columns to games table
    op.add_column('games', sa.Column('creator_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True))
    op.add_column('games', sa.Column('status', sa.Enum(GameStatus, name='gamestatus', native_enum=True), server_default='setup'))
    op.add_column('games', sa.Column('language', sa.String, server_default='de'))
    op.add_column('games', sa.Column('max_players', sa.Integer, server_default='2'))
    op.add_column('games', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.add_column('games', sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('games', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    
    # Make creator_id non-nullable after adding it
    op.execute('UPDATE games SET creator_id = current_player_id WHERE creator_id IS NULL')
    op.alter_column('games', 'creator_id', nullable=False)

def downgrade():
    # Remove columns in reverse order
    op.drop_column('games', 'completed_at')
    op.drop_column('games', 'started_at')
    op.drop_column('games', 'created_at')
    op.drop_column('games', 'max_players')
    op.drop_column('games', 'language')
    op.drop_column('games', 'status')
    op.drop_column('games', 'creator_id')
    
    # Drop the enum type
    op.execute('DROP TYPE gamestatus') 