from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '8ddb989f97a0'
down_revision: Union[str, None] = '4e7326941b28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('import_batches', 'raw_data',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               nullable=False)
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_users_deleted_at'), 'users', ['deleted_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_deleted_at'), table_name='users')
    op.drop_column('users', 'deleted_at')
    op.alter_column('import_batches', 'raw_data',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               nullable=True)
