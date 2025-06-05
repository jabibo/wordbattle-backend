"""Add invitation preferences to users

Revision ID: 0007
Revises: 0006
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    # Add invitation preference columns to users table
    op.add_column('users', sa.Column('allow_invites', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('preferred_languages', sa.JSON(), nullable=True))
    
    # Set default preferred languages for existing users
    op.execute("UPDATE users SET preferred_languages = '[\"en\", \"de\"]' WHERE preferred_languages IS NULL")


def downgrade():
    # Remove invitation preference columns
    op.drop_column('users', 'preferred_languages')
    op.drop_column('users', 'allow_invites') 