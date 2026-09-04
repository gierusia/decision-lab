import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.decisions.deps import get_decision_or_404
from app.decisions.models import Decision
from app.experiments import service
from app.experiments.models import Experiment


def get_experiment_or_404(
    experiment_id: uuid.UUID,
    decision: Decision = Depends(get_decision_or_404),
    db: Session = Depends(get_db),
) -> Experiment:
    experiment = service.get_experiment(db, decision, experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    return experiment
