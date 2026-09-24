from sqlalchemy.orm import Session

from app.models.role import Role


def get_by_name(db: Session, name: str) -> Role | None:
    return db.query(Role).filter(Role.name == name).first()


def get_by_names(db: Session, names: list[str]) -> list[Role]:
    if not names:
        return []
    return db.query(Role).filter(Role.name.in_(names)).all()
