"""Контракт ответов dashboard / summary.

Сборка полей — в service (следующий шаг). Здесь только форма JSON
и инварианты счётчиков: все ключи статусов/вердиктов присутствуют,
даже если нули.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.dashboard.readiness import DecisionReadiness
from app.decisions.models import DecisionStatus
from app.experiments.models import ExperimentStatus


class DashboardAuthorOut(BaseModel):
    id: uuid.UUID
    full_name: str | None


class ExperimentStatusCounts(BaseModel):
    planned: int = 0
    running: int = 0
    completed: int = 0


class VerdictCounts(BaseModel):
    success: int = 0
    partial: int = 0
    failed: int = 0


class DecisionStatusCounts(BaseModel):
    draft: int = 0
    active: int = 0
    needs_revision: int = 0
    completed: int = 0
    cancelled: int = 0


class DashboardFiltersEcho(BaseModel):
    date_from: datetime | None
    date_to: datetime | None
    status: DecisionStatus | None
    author_id: uuid.UUID | None
    stale_only: bool


class DashboardPaginationOut(BaseModel):
    limit: int
    offset: int
    total: int


class DashboardTotalsOut(BaseModel):
    decisions: int
    by_status: DecisionStatusCounts
    stale: int
    experiments_open: int
    experiments_completed: int
    verdicts: VerdictCounts


class DashboardDecisionOut(BaseModel):
    id: uuid.UUID
    title: str
    status: DecisionStatus
    tags: list[str]
    author: DashboardAuthorOut
    created_at: datetime
    updated_at: datetime
    is_stale: bool
    readiness: DecisionReadiness
    experiment_counts: ExperimentStatusCounts
    verdict_counts: VerdictCounts


class DashboardOut(BaseModel):
    filters: DashboardFiltersEcho
    pagination: DashboardPaginationOut
    totals: DashboardTotalsOut
    decisions: list[DashboardDecisionOut]


class OpenExperimentOut(BaseModel):
    id: uuid.UUID
    metric_name: str
    status: ExperimentStatus
    created_by: uuid.UUID


class SummaryExperimentsOut(BaseModel):
    total: int
    by_status: ExperimentStatusCounts
    verdicts: VerdictCounts
    open: list[OpenExperimentOut]


class DecisionSummaryOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: DecisionStatus
    tags: list[str]
    author: DashboardAuthorOut
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_stale: bool
    stale_threshold_days: int
    stale_after_at: datetime | None
    age_seconds: int = Field(ge=0)
    readiness: DecisionReadiness
    experiments: SummaryExperimentsOut
