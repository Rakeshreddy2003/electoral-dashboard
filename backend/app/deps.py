from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.config import settings
from app.database import get_db
from app.models import Role, User

# auto_error=False -- when auth is disabled there's no token to require in
# the first place, so a missing Authorization header must not 401 before
# get_current_user ever gets a chance to check settings.auth_disabled.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _bypass_user() -> User:
    """Synthetic admin user for AUTH_DISABLED=true -- never persisted, just
    carries the fields the rest of the app reads (email for audit logs,
    role for permission checks)."""
    return User(email="everyone@local", full_name="Everyone (auth disabled)", role=Role.admin, is_active=True)


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if settings.auth_disabled:
        return _bypass_user()
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_roles(*allowed: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return checker


require_any = require_roles(Role.admin, Role.analyst, Role.viewer)
require_analyst_or_admin = require_roles(Role.admin, Role.analyst)
require_admin = require_roles(Role.admin)
