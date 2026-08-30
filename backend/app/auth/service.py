from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.security import hash_password, pwd_context, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str, full_name: str | None = None) -> User:
    user = User(email=email, password_hash=hash_password(password), full_name=full_name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Проверка в роутере (get_user_by_email) закрывает обычный случай,
        # но не гонку: два одновременных register с одним email оба могут
        # пройти ту проверку раньше, чем сюда долетит commit. Уникальный
        # индекс на email — настоящая линия защиты, эта ветка её просто
        # превращает в понятную ошибку вместо голого 500.
        db.rollback()
        raise ValueError("Email already registered") from None
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)

    if user is None:
        # Без этого вызова ответ для "такого email нет" был бы заметно
        # быстрее ответа для "email есть, пароль неверный" (там всегда
        # считается argon2-хэш) — по этой разнице во времени можно было бы
        # перебором узнавать, какие email зарегистрированы, не подбирая
        # ни одного пароля. dummy_verify тратит примерно то же время,
        # что и настоящая проверка, но всегда возвращает False.
        pwd_context.dummy_verify()
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
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        user.password_hash = hash_password(new_password)

    db.commit()
    db.refresh(user)
    return user
