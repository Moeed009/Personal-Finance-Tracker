import uuid

from pydantic import BaseModel, Field

from app.models.category import CategoryType
from app.schemas.common import ORMModel


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: CategoryType


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class CategoryRead(ORMModel):
    id: uuid.UUID
    name: str
    type: CategoryType
    is_default: bool
