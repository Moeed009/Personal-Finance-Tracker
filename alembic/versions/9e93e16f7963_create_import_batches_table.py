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
