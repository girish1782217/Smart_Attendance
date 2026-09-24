from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog


def log(
    db: Session,
    *,
    actor_user_id: int,
    action: AuditAction,
    entity_type: str,
    entity_id: int,
    before_value: str | None = None,
    after_value: str | None = None,
    reason: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action.value,
        entity_type=entity_type,
        entity_id=entity_id,
        before_value=before_value,
        after_value=after_value,
        reason=reason,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
