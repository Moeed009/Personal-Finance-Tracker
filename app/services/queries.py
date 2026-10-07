import uuid

from sqlalchemy import and_

from app.models.transaction import TransactionType
from app.models.transaction import Transaction


def analysis_scope(user_id: uuid.UUID):
    return and_(
        Transaction.user_id == user_id,
        Transaction.transfer_group_id.is_(None),
        Transaction.type != TransactionType.TRANSFER,
    )
