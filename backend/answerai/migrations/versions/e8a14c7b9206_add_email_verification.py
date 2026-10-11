"""Add email verification without locking out existing accounts."""

import sqlalchemy as sa
from alembic import op

revision = 'e8a14c7b9206'
down_revision = 'b8f2c6d91a04'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('auth', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table(
        'email_verification',
        sa.Column('user_id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=True, unique=True),
        sa.Column('expires_at', sa.BigInteger(), nullable=False),
        sa.Column('sent_at', sa.BigInteger(), nullable=False),
    )


def downgrade():
    op.drop_table('email_verification')
    with op.batch_alter_table('auth') as batch:
        batch.drop_column('email_verified')
