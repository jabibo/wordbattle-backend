"""Add push notification support

Revision ID: 0011_add_push_notifications
Revises: 0010_add_game_name_and_ended_at
Create Date: 2026-02-15

"""
from alembic import op
import sqlalchemy as sa


revision = '0011_add_push_notifications'
down_revision = '0010_add_game_name_and_ended_at'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'push_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String(512), nullable=False),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('app_version', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    op.create_index('ix_push_tokens_user_id', 'push_tokens', ['user_id'])
    op.create_index('ix_push_tokens_token', 'push_tokens', ['token'], unique=True)

    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('game_moves', sa.Boolean(), default=True),
        sa.Column('invitations', sa.Boolean(), default=True),
        sa.Column('game_completion', sa.Boolean(), default=True),
        sa.Column('chat_messages', sa.Boolean(), default=True),
        sa.Column('quiet_hours_enabled', sa.Boolean(), default=False),
        sa.Column('quiet_hours_start', sa.String(5)),
        sa.Column('quiet_hours_end', sa.String(5)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'], unique=True)

    op.create_table(
        'notification_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('game_id', sa.String(36)),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('success', sa.Boolean()),
        sa.Column('error_message', sa.Text()),
    )
    op.create_index('ix_notification_log_user_id', 'notification_log', ['user_id'])
    op.create_index('ix_notification_log_sent_at', 'notification_log', ['sent_at'])


def downgrade() -> None:
    op.drop_index('ix_notification_log_sent_at', table_name='notification_log')
    op.drop_index('ix_notification_log_user_id', table_name='notification_log')
    op.drop_table('notification_log')

    op.drop_index('ix_notification_preferences_user_id', table_name='notification_preferences')
    op.drop_table('notification_preferences')

    op.drop_index('ix_push_tokens_token', table_name='push_tokens')
    op.drop_index('ix_push_tokens_user_id', table_name='push_tokens')
    op.drop_table('push_tokens')
