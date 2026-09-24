from datetime import datetime

from sqlalchemy.orm import Session

from app.core.time_utils import utc_now
from app.models.revoked_token import RevokedToken


def is_revoked(db: Session, jti: str) -> bool:
    return db.get(RevokedToken, jti) is not None


def revoke(db: Session, *, jti: str, expires_at: datetime) -> None:
    # Opportunistic cleanup so this table doesn't grow unbounded — safe
    # because a token past its own expiry can never authenticate anyway.
    db.query(RevokedToken).filter(RevokedToken.expires_at < utc_now()).delete()
    db.add(RevokedToken(jti=jti, expires_at=expires_at))
    db.commit()
