"""Add feedback system

Revision ID: 63f920666b37
Revises: 0008_drop_friends_table
Create Date: 2025-06-14 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '63f920666b37'
down_revision = '0008'
branch_labels = None
depends_on = None

def upgrade():
    # Create feedback table
    op.create_table('feedback',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Enum('BUG_REPORT', 'FEATURE_REQUEST', 'PERFORMANCE_ISSUE', 'UI_UX_FEEDBACK', 'GAME_LOGIC_ISSUE', 'AUTHENTICATION_PROBLEM', 'NETWORK_CONNECTION_ISSUE', 'GENERAL_FEEDBACK', 'OTHER', name='feedbackcategory'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'IN_REVIEW', 'RESOLVED', 'CLOSED', name='feedbackstatus'), nullable=False),
        sa.Column('debug_logs', sa.JSON(), nullable=True),
        sa.Column('device_info', sa.JSON(), nullable=True),
        sa.Column('app_info', sa.JSON(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'])
    op.create_index('ix_feedback_category', 'feedback', ['category'])
    op.create_index('ix_feedback_status', 'feedback', ['status'])
    op.create_index('ix_feedback_created_at', 'feedback', ['created_at'])

def downgrade():
    # Drop indexes
    op.drop_index('ix_feedback_created_at', table_name='feedback')
    op.drop_index('ix_feedback_status', table_name='feedback')
    op.drop_index('ix_feedback_category', table_name='feedback')
    op.drop_index('ix_feedback_user_id', table_name='feedback')
    
    # Drop table
    op.drop_table('feedback')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS feedbackstatus')
    op.execute('DROP TYPE IF EXISTS feedbackcategory')