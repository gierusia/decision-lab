import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator

MIN_PASSWORD_LENGTH = 8


def _ensure_password_is_strong_enough(password: str) -> str:
    # Длина — это то место, где реально ошибаются живые пользователи.
    # Требовать спецсимволы/цифры на MVP-этапе смысла нет — это добавляет
    # раздражения, но почти не добавляет безопасности.
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return _ensure_password_is_strong_enough(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    created_at: datetime
    is_admin: bool = False

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdateRequest(BaseModel):
    """И имя, и смена пароля идут через один эндпоинт — оба поля опциональны,
    можно менять что-то одно или сразу оба."""

    full_name: str | None = None
    current_password: str | None = None
    new_password: str | None = None

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, value: str | None) -> str | None:
        return value if value is None else _ensure_password_is_strong_enough(value)

    @model_validator(mode="after")
    def _current_password_required_for_change(self) -> "ProfileUpdateRequest":
        # Проверяем именно на уровне схемы, а не в роутере — это условие
        # формы запроса, а не бизнес-логика вокруг хранения пароля.
        if self.new_password and not self.current_password:
            raise ValueError("current_password is required to set a new password")
        return self
