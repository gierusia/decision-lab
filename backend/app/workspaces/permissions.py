"""Иерархия прав в workspace.

Owner умеет всё, что умеет Member; Member умеет всё, что умеет Viewer.
Поэтому проверка прав — это не "роль совпадает", а "ранг роли не ниже
требуемого". FastAPI-обвязка вокруг этой проверки живёт в deps.py 
здесь только чистая логика, без Depends и HTTPException, чтобы её можно
было протестировать без поднятия приложения.
"""

from app.workspaces.models import WorkspaceRole

_ROLE_RANK: dict[WorkspaceRole, int] = {
    WorkspaceRole.VIEWER: 1,
    WorkspaceRole.MEMBER: 2,
    WorkspaceRole.OWNER: 3,
}


def has_role(actual_role: WorkspaceRole, min_role: WorkspaceRole) -> bool:
    return _ROLE_RANK[actual_role] >= _ROLE_RANK[min_role]
