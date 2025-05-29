"""Add friends table

Revision ID: 0006
Revises: 0005
Create Date: 2025-05-28 07:41:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

def upgrade():
    # Create friends table
    op.create_table('friends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('friend_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['friend_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'friend_id', name='unique_friendship')
    )
    op.create_index(op.f('ix_friends_id'), 'friends', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_friends_id'), table_name='friends')
    op.drop_table('friends') 