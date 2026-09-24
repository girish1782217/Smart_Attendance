from sqlalchemy.orm import Session

from app.models.user import User


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create(
    db: Session,
    *,
    email: str,
    full_name: str,
    hashed_password: str,
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, *, page: int, page_size: int) -> tuple[list[User], int]:
    query = db.query(User).order_by(User.id)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
