"""Add durable agent execution state without changing conversation records."""

import sqlalchemy as sa
from alembic import op

revision = 'd90ac81f2e10'
down_revision = 'c7d1e32b8a09'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'agent_run',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('request_key', sa.String(), nullable=False),
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('checkpoint', sa.JSON(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('timeline', sa.JSON(), nullable=False),
        sa.Column('event_sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('token_budget', sa.Integer(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('lease', sa.String(), nullable=True),
        sa.Column('lease_until', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.Column('deadline', sa.BigInteger(), nullable=False),
        sa.Column('iterations', sa.Integer(), nullable=False),
        sa.Column('max_seconds', sa.Integer(), nullable=False),
        sa.Column('resume_count', sa.Integer(), nullable=False),
        sa.UniqueConstraint('user_id', 'request_key', name='uq_agent_run_request'),
    )
    op.create_table(
        'agent_owner_lease',
        sa.Column('user_id', sa.String(), primary_key=True),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('lease', sa.String(), nullable=False),
        sa.Column('lease_until', sa.BigInteger(), nullable=False),
    )
    op.create_index('ix_agent_run_user_id', 'agent_run', ['user_id'])
    op.create_index('ix_agent_run_status', 'agent_run', ['status'])


def downgrade():
    op.drop_table('agent_owner_lease')
    op.drop_table('agent_run')
