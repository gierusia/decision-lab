"""Зависимости, которые будут переиспользоваться и на следующих этапах
(workspaces, decisions и так далее подключаются поверх get_current_user)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    try:
        # user_id — строка из тела JWT. Токен подписан нами же, так что
        # обычно там валидный UUID, но если кто-то вручную подсунет битую
        # строку (например, при тестировании curl'ом), GUID-колонка
        # попытается сделать uuid.UUID(value) и упадёт с ValueError —
        # ловим здесь, а не даём этому долететь до 500.
        user = db.query(User).filter(User.id == user_id).first()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from None

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
