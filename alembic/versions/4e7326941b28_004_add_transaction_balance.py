"""004_add_transaction_balance

Revision ID: 4e7326941b28
Revises: 9e93e16f7963
Create Date: 2026-10-01 10:16:11.261471
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4e7326941b28"
down_revision: Union[str, None] = "9e93e16f7963"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("balance", sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "balance")