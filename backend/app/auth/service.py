from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str, full_name: str | None = None) -> User:
    user = User(email=email, password_hash=hash_password(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def update_profile(
    db: Session,
    user: User,
    full_name: str | None,
    current_password: str | None,
    new_password: str | None,
) -> User:
    if full_name is not None:
        user.full_name = full_name

    if new_password is not None:
        # current_password к этому моменту уже гарантированно передан —
        # это проверяется в ProfileUpdateRequest, — но сам факт, что он
        # верный, можно проверить только здесь, рядом с хэшем.
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        user.password_hash = hash_password(new_password)

    db.commit()
    db.refresh(user)
    return user
