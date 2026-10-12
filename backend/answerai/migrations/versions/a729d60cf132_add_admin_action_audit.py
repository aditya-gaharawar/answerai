"""Add an admin action ledger without storing credentials or raw request bodies."""

import sqlalchemy as sa
from alembic import op

revision = 'a729d60cf132'
down_revision = 'f31a902ecb70'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'admin_action',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('actor_id', sa.String(), nullable=False),
        sa.Column('target_id', sa.String()),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
    )
    op.create_index('ix_admin_action_created_at', 'admin_action', ['created_at'])
    op.create_index('ix_billing_usage_starts_at', 'billing_usage', ['starts_at'])


def downgrade():
    op.drop_index('ix_billing_usage_starts_at', table_name='billing_usage')
    op.drop_table('admin_action')
