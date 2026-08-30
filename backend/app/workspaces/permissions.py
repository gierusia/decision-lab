"""Каркас проверки прав в workspace.

Сейчас реализована только одна проверка — "владелец ли это workspace",
потому что участников кроме Owner пока просто неоткуда взять (add-member
эндпоинта ещё нет). Как только появится приглашение участников:

- добавится has_role(workspace, user, min_role) — сравнение по иерархии
  Owner > Member > Viewer вместо точного совпадения ролей
- require_role() ниже перестанет быть заглушкой и будет использоваться
  как FastAPI-зависимость на эндпоинтах Decisions/Experiments
"""

from app.auth.models import User
from app.workspaces.models import Workspace


def is_owner(workspace: Workspace, user: User) -> bool:
    return workspace.owner_id == user.id


def require_role(min_role: str):
    """Заглушка на будущее — превратится в зависимость вида
    Depends(require_role("member")), когда появятся Member/Viewer.
    Пока не вызывается нигде в коде."""
    raise NotImplementedError("Роли Member/Viewer появятся во второй части Этапа 2")
