"""Заливка демо-данных. Не вызывается при старте приложения.

  cd backend && python -m app.seed

Повторный запуск не плодит вторую Demo Lab.
Домен почты и пароль демо-юзеров: SEED_EMAIL_DOMAIN, SEED_PASSWORD.
"""

from decimal import Decimal

from app.auth.service import create_user, get_user_by_email
from app.core.admins import load_admin_accounts
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.seed_admins import seed_admins
from app.decisions.models import Decision, DecisionStatus, DecisionTag
from app.experiments.models import Experiment, ExperimentStatus, MetricDirection
from app.experiments.verdict import compute_verdict
from app.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole
from app.workspaces.service import assign_membership, get_membership


DEMO_WORKSPACE = "Demo Lab"
DEMO_PASSWORD_FALLBACK = "demo-pass-12"


def _domain() -> str:
    return getattr(settings, "SEED_EMAIL_DOMAIN", None) or "example.com"


def _password() -> str:
    return getattr(settings, "SEED_PASSWORD", None) or DEMO_PASSWORD_FALLBACK


def _get_or_create_user(db, email: str, full_name: str):
    user = get_user_by_email(db, email)
    if user is not None:
        return user
    return create_user(db, email, _password(), full_name)


def _get_or_create_workspace(db, owner) -> Workspace:
    existing = db.query(Workspace).filter(Workspace.name == DEMO_WORKSPACE).first()
    if existing is not None:
        return existing
    workspace = Workspace(name=DEMO_WORKSPACE, owner_id=owner.id, stale_threshold_days=30)
    db.add(workspace)
    db.flush()
    db.add(
        WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner.id,
            role=WorkspaceRole.OWNER,
        )
    )
    db.commit()
    db.refresh(workspace)
    return workspace


def _ensure_role(db, workspace: Workspace, user, role: WorkspaceRole, actor) -> None:
    membership = get_membership(db, workspace, user)
    if membership is not None:
        return
    assign_membership(db, str(user.id), str(workspace.id), role, actor=actor)


def _get_or_create_decision(db, workspace: Workspace, owner, title: str, description: str, tags: list[str], status: DecisionStatus) -> Decision:
    decision = (
        db.query(Decision)
        .filter(Decision.workspace_id == workspace.id, Decision.title == title)
        .first()
    )
    if decision is None:
        decision = Decision(
            workspace_id=workspace.id,
            title=title,
            description=description,
            status=status,
            created_by=owner.id,
            tags=[DecisionTag(tag=tag) for tag in tags],
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision
    decision.description = description
    decision.status = status
    db.commit()
    db.refresh(decision)
    return decision


def _get_or_create_experiment(
    db,
    decision: Decision,
    owner,
    metric_name: str,
    direction: MetricDirection,
    target,
    actual,
    tolerance,
    status: ExperimentStatus,
    flag: str | None = None,
    notes: str | None = None,
) -> None:
    experiment = (
        db.query(Experiment)
        .filter(Experiment.decision_id == decision.id, Experiment.metric_name == metric_name)
        .first()
    )
    target_d = Decimal(str(target))
    actual_d = None if actual is None else Decimal(str(actual))
    tol_d = Decimal(str(tolerance))
    verdict = None
    if status == ExperimentStatus.COMPLETED and actual_d is not None:
        verdict = compute_verdict(direction, target_d, actual_d, tol_d)
    if experiment is None:
        experiment = Experiment(
            decision_id=decision.id,
            created_by=owner.id,
            status=status,
            verdict=verdict,
            metric_name=metric_name,
            metric_direction=direction,
            target_value=target_d,
            actual_value=actual_d,
            partial_tolerance_percent=tol_d,
            notes=notes,
            feature_flag_key=flag,
            is_frozen=status == ExperimentStatus.COMPLETED,
        )
        db.add(experiment)
    else:
        experiment.status = status
        experiment.verdict = verdict
        experiment.target_value = target_d
        experiment.actual_value = actual_d
        experiment.partial_tolerance_percent = tol_d
        experiment.metric_direction = direction
        experiment.notes = notes
        experiment.feature_flag_key = flag
        experiment.is_frozen = status == ExperimentStatus.COMPLETED
    db.commit()


def run() -> None:
    seed_admins()
    accounts = load_admin_accounts()
    if not accounts:
        raise SystemExit("config_admin.yaml пуст — некого делать owner Demo Lab")

    db = SessionLocal()
    try:
        owner = get_user_by_email(db, accounts[0].email)
        if owner is None:
            raise SystemExit(f"Админ {accounts[0].email} не создан. Перезапусти backend.")

        domain = _domain()
        member = _get_or_create_user(db, f"member@{domain}", "Demo Member")
        viewer = _get_or_create_user(db, f"viewer@{domain}", "Demo Viewer")

        workspace = _get_or_create_workspace(db, owner)
        _ensure_role(db, workspace, member, WorkspaceRole.MEMBER, owner)
        _ensure_role(db, workspace, viewer, WorkspaceRole.VIEWER, owner)

        onboarding = _get_or_create_decision(
            db,
            workspace,
            owner,
            "Онбординг",
            "Как быстрее доводим новичка до первого полезного коммита.",
            ["onboarding", "people"],
            DecisionStatus.ACTIVE,
        )
        _get_or_create_experiment(
            db, onboarding, owner,
            "дни до первого PR", MetricDirection.LOWER_IS_BETTER,
            14, None, 10, ExperimentStatus.PLANNED, notes="ещё не стартовали набор",
        )
        _get_or_create_experiment(
            db, onboarding, owner,
            "доля прошедших чек-лист", MetricDirection.HIGHER_IS_BETTER,
            80, 62, 10, ExperimentStatus.RUNNING, notes="идёт пилот на одной команде",
        )

        recs = _get_or_create_decision(
            db,
            workspace,
            owner,
            "Новый алгоритм рекомендаций",
            "Меняем выдачу рекомендаций и смотрим CTR и precision.",
            ["recommendations", "ml"],
            DecisionStatus.ACTIVE,
        )
        _get_or_create_experiment(
            db, recs, owner,
            "CTR выдачи", MetricDirection.HIGHER_IS_BETTER,
            8, 8.4, 5, ExperimentStatus.COMPLETED, flag="recs-v2",
        )
        _get_or_create_experiment(
            db, recs, owner,
            "precision@10", MetricDirection.HIGHER_IS_BETTER,
            40, 38, 10, ExperimentStatus.COMPLETED,
        )

        tariff = _get_or_create_decision(
            db,
            workspace,
            owner,
            "Платный тариф",
            "Проверяем, тянет ли новый прайс конверсию в оплату.",
            ["billing", "pricing"],
            DecisionStatus.COMPLETED,
        )
        _get_or_create_experiment(
            db, tariff, owner,
            "конверсия в оплату", MetricDirection.HIGHER_IS_BETTER,
            12, 7, 5, ExperimentStatus.COMPLETED,
        )

        print(f"Demo Lab готова. Админ: {owner.email}")
        print(f"Member: member@{domain}  Viewer: viewer@{domain}")
        print(f"Пароль демо-юзеров: {_password()}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
