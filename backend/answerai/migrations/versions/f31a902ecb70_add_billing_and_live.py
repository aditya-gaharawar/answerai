"""Add plans, billing, shared quotas, and Live Calls leases."""

import sqlalchemy as sa
from alembic import op

revision = 'f31a902ecb70'
down_revision = 'e8a14c7b9206'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'billing_account',
        sa.Column('user_id', sa.String(), primary_key=True),
        sa.Column('override', sa.String(), nullable=False),
        sa.Column('override_until', sa.BigInteger(), nullable=False),
        sa.Column('checkout_until', sa.BigInteger(), nullable=False),
    )
    op.create_table(
        'billing_subscription',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('checkout_id', sa.String(), unique=True),
        sa.Column('provider_id', sa.String(), unique=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('period_end', sa.BigInteger(), nullable=False),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('reconciled_at', sa.BigInteger(), nullable=False),
    )
    op.create_index('ix_billing_subscription_user_id', 'billing_subscription', ['user_id'])
    op.create_table(
        'billing_event',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
    )
    op.create_table(
        'billing_usage',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('metric', sa.String(), nullable=False),
        sa.Column('window', sa.Integer(), nullable=False),
        sa.Column('starts_at', sa.BigInteger(), nullable=False),
        sa.Column('used', sa.Integer(), nullable=False),
    )
    op.create_index('ix_billing_usage_user_id', 'billing_usage', ['user_id'])
    op.create_table(
        'live_lease',
        sa.Column('user_id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('expires_at', sa.BigInteger(), nullable=False),
    )


def downgrade():
    for table in ['live_lease', 'billing_usage', 'billing_event', 'billing_subscription', 'billing_account']:
        op.drop_table(table)
