"""Add wordlists table for multi-language support

Revision ID: multilang_wordlists
Revises: 03014fa14d00
Create Date: 2025-05-23 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'multilang_wordlists'
down_revision = '03014fa14d00'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create wordlists table
    op.create_table('wordlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('word', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for faster lookups
    op.create_index('idx_word_language', 'wordlists', ['word', 'language'], unique=False)
    
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_word_language', table_name='wordlists')
    
    # Drop wordlists table
    op.drop_table('wordlists')
    
    # Drop is_admin column from users table
    op.drop_column('users', 'is_admin')