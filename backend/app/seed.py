"""
One-off script to create the first admin user (and optionally sample
analyst/viewer accounts for testing). Run with:

    python -m app.seed admin@crawindia.com "Full Name" Str0ngPassword! admin

Role must be one of: admin, analyst, viewer.
"""

import sys

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Role, User


def main() -> None:
    if len(sys.argv) != 5:
        print("Usage: python -m app.seed <email> <full_name> <password> <role>")
        sys.exit(1)

    email, full_name, password, role_str = sys.argv[1:5]
    try:
        role = Role(role_str)
    except ValueError:
        print(f"Invalid role '{role_str}'. Must be one of: admin, analyst, viewer")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User {email} already exists; updating password/role.")
            existing.hashed_password = hash_password(password)
            existing.role = role
            existing.full_name = full_name
        else:
            db.add(
                User(
                    email=email,
                    full_name=full_name,
                    hashed_password=hash_password(password),
                    role=role,
                    is_active=True,
                )
            )
        db.commit()
        print(f"OK: {email} set as {role.value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
