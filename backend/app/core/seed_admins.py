from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import create_user, get_user_by_email
from app.core.admins import load_admin_accounts
from app.core.database import SessionLocal


def seed_admins() -> None:
    accounts = load_admin_accounts()
    if not accounts:
        return
    db: Session = SessionLocal()
    try:
        for account in accounts:
            if get_user_by_email(db, account.email) is not None:
                continue
            create_user(db, account.email, account.password, account.full_name)
    finally:
        db.close()
