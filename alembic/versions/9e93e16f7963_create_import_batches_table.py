"""add raw_data to import batches

Revision ID: 9e93e16f7963
Revises: 001
Create Date: 2026-09-30 12:18:51.207501

This revision used to create every table again, which made
`alembic upgrade head` fail on an empty database because 001 had already
created them. The only real change it carried was the raw_data column on
import_batches, so that is all it does now. Databases that already ran the
old version are unaffected: Alembic never re-runs an applied revision.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '9e93e16f7963'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.add_column(
        'import_batches',
        sa.Column('raw_data', JSON_TYPE, nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column('import_batches', 'raw_data')