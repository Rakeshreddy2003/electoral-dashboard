from sqlalchemy.orm import Session

from app.models import AuditLog


def record(db: Session, user_email: str, action: str, resource: str, detail: str | None = None) -> None:
    db.add(AuditLog(user_email=user_email, action=action, resource=resource, detail=detail))
    db.commit()
