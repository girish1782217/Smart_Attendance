from typing import Generic, TypeVar

from sqlalchemy import or_
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class CRUDBase(Generic[ModelT]):
    """Shared list/get/create/update/soft-delete logic for the master-data
    entities (SPEC 04), which all share an identical CRUD shape. Business
    validation (uniqueness messages, FK existence checks) stays in each
    entity's own service module — this class only knows how to talk to one
    table generically.
    """

    def __init__(self, model: type[ModelT]):
        self.model = model

    def get_by_id(self, db: Session, id_: int) -> ModelT | None:
        return db.get(self.model, id_)

    def list_paginated(
        self,
        db: Session,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        search_fields: tuple[str, ...] = (),
        filters: dict[str, object] | None = None,
    ) -> tuple[list[ModelT], int]:
        query = db.query(self.model)

        if filters:
            for attr, value in filters.items():
                if value is not None:
                    query = query.filter(getattr(self.model, attr) == value)

        if search and search_fields:
            like_pattern = f"%{search}%"
            query = query.filter(
                or_(*(getattr(self.model, field).ilike(like_pattern) for field in search_fields))
            )

        total = query.count()
        items = query.order_by(self.model.id).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create(self, db: Session, obj: ModelT) -> ModelT:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj: ModelT, fields: dict[str, object]) -> ModelT:
        for key, value in fields.items():
            if value is not None:
                setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    def soft_delete(self, db: Session, obj: ModelT) -> ModelT:
        obj.is_active = False
        db.commit()
        db.refresh(obj)
        return obj
