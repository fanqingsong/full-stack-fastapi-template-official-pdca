"""Feature extraction from PDCA cycles for causal analysis."""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlmodel import select
import pandas as pd

from app.pdca.models import PDCACycle, ExecutionLog


def extract_pdca_features(
    db: Session,
    cycle_ids: List[uuid.UUID],
    owner_id: Optional[uuid.UUID] = None
) -> pd.DataFrame:
    """
    Extract causal analysis features from PDCA cycles.

    Features extracted:
    - Outcomes: success (binary), duration_hours, error_count
    - Treatments: agent_type, has_parent, num_children
    - Confounders: created_hour, day_of_week

    Args:
        db: Database session
        cycle_ids: List of cycle IDs to extract features from
        owner_id: Optional owner filter

    Returns:
        DataFrame with extracted features
    """
    if not cycle_ids:
        return pd.DataFrame()

    # Build query
    query = select(PDCACycle).where(PDCACycle.id.in_(cycle_ids))
    if owner_id:
        query = query.where(PDCACycle.owner_id == owner_id)

    cycles = db.exec(query).all()

    if not cycles:
        return pd.DataFrame()

    # Collect all cycle IDs for batch error count query
    cycle_id_list = [cycle.id for cycle in cycles]

    # Single aggregated query to get error counts for all cycles
    error_count_map = {}
    if cycle_id_list:
        error_counts = db.exec(
            select(
                ExecutionLog.cycle_id,
                func.count(ExecutionLog.id).label("count")
            )
            .where(
                ExecutionLog.cycle_id.in_(cycle_id_list),
                ExecutionLog.level == "error"
            )
            .group_by(ExecutionLog.cycle_id)
        ).all()

        # Create a mapping for easy lookup
        error_count_map = {row.cycle_id: row.count for row in error_counts}

    features = []
    for cycle in cycles:
        # Calculate cycle duration
        duration_hours = 0
        if cycle.started_at and cycle.completed_at:
            duration = cycle.completed_at - cycle.started_at
            duration_hours = duration.total_seconds() / 3600

        # Get error count from pre-fetched map (defaults to 0 if no errors)
        error_count = error_count_map.get(cycle.id, 0)

        # Extract features
        feature_row = {
            # Identifiers
            "cycle_id": str(cycle.id),
            "name": cycle.name,

            # Outcome variables
            "success": 1 if cycle.phase == "completed" else 0,
            "failed": 1 if cycle.phase == "failed" else 0,
            "duration_hours": duration_hours,
            "error_count": error_count,

            # Treatment variables
            "agent_type": cycle.agent_type or "unknown",
            "has_parent": 1 if cycle.parent_id else 0,
            "num_children": len(cycle.children) if cycle.children else 0,

            # Confounders
            "owner_id": str(cycle.owner_id),
            "created_hour": cycle.created_at.hour if cycle.created_at else 0,
            "day_of_week": cycle.created_at.weekday() if cycle.created_at else 0,
        }

        features.append(feature_row)

    return pd.DataFrame(features)


def get_available_variables() -> list[str]:
    """
    Get list of variables available for causal analysis.

    Returns:
        List of variable names with descriptions
    """
    return [
        "success - Whether cycle completed successfully (binary)",
        "failed - Whether cycle failed (binary)",
        "duration_hours - Cycle execution time in hours (continuous)",
        "error_count - Number of error logs (count)",
        "agent_type - Type of agent used (categorical)",
        "has_parent - Whether cycle has a parent (binary)",
        "num_children - Number of child cycles (count)",
    ]


def get_user_cycle_ids(db: Session, user_id: uuid.UUID, filters: dict = None) -> List[uuid.UUID]:
    """Get cycle IDs for user."""
    query = select(PDCACycle.id).where(PDCACycle.owner_id == user_id)

    # Apply filters if provided
    if filters:
        # MVP: No complex filtering
        pass

    cycles = db.exec(query).all()
    return [cycle.id for cycle in cycles]
