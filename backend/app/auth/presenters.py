from app.auth.models import User
from app.auth.schemas import UserOut
from app.core.admins import is_platform_admin


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        is_admin=is_platform_admin(user.email),
    )
