"""Граф допустимых переходов статуса эксперимента.

completed — терминальный. planned → completed в обход running запрещён:
факт без фазы запуска смешивает черновик и итог, и вердикт тогда
непонятно в какой момент считать.
"""

from app.experiments.models import ExperimentStatus

_ALLOWED_TRANSITIONS: dict[ExperimentStatus, set[ExperimentStatus]] = {
    ExperimentStatus.PLANNED: {ExperimentStatus.RUNNING},
    ExperimentStatus.RUNNING: {ExperimentStatus.COMPLETED},
    ExperimentStatus.COMPLETED: set(),
}


def is_transition_allowed(current: ExperimentStatus, target: ExperimentStatus) -> bool:
    if current == target:
        return True
    return target in _ALLOWED_TRANSITIONS[current]
