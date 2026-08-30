"""Граф допустимых переходов статуса решения.

completed и cancelled — терминальные: попытка сменить статус решения,
которое уже находится в одном из них, всегда отклоняется. needs_revision
не тупиковый — из него можно вернуться в active, доработав решение.
"""

from app.decisions.models import DecisionStatus

_ALLOWED_TRANSITIONS: dict[DecisionStatus, set[DecisionStatus]] = {
    DecisionStatus.DRAFT: {DecisionStatus.ACTIVE, DecisionStatus.CANCELLED},
    DecisionStatus.ACTIVE: {
        DecisionStatus.NEEDS_REVISION,
        DecisionStatus.COMPLETED,
        DecisionStatus.CANCELLED,
    },
    DecisionStatus.NEEDS_REVISION: {DecisionStatus.ACTIVE, DecisionStatus.CANCELLED},
    DecisionStatus.COMPLETED: set(),
    DecisionStatus.CANCELLED: set(),
}


def is_transition_allowed(current: DecisionStatus, target: DecisionStatus) -> bool:
    if current == target:
        # PATCH с тем же статусом, что уже стоит — не ошибка, а no-op.
        return True
    return target in _ALLOWED_TRANSITIONS[current]
