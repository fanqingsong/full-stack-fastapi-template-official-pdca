"""Tests for PDCA data extraction."""

import pytest
import pandas as pd
from sqlmodel import Session, select
from app.models import User
from app.pdca.models import PDCACycle, ExecutionLog
from app.causal.data_extractor import extract_pdca_features
from .factories import create_test_user


def test_extract_pdca_features_basic(db_session):
    """Test basic feature extraction from PDCA cycles."""
    # Create user
    user = create_test_user(db_session)

    # Create test cycles
    cycle1 = PDCACycle(
        name="Test Cycle 1",
        phase="completed",
        status="completed",
        owner_id=user.id,
        agent_type="openai"
    )
    cycle2 = PDCACycle(
        name="Test Cycle 2",
        phase="failed",
        status="failed",
        owner_id=user.id,
        agent_type="python_script"
    )

    db_session.add(cycle1)
    db_session.add(cycle2)
    db_session.commit()

    # Extract features
    features = extract_pdca_features(
        db=db_session,
        cycle_ids=[cycle1.id, cycle2.id]
    )

    # Verify structure
    assert isinstance(features, pd.DataFrame)
    assert len(features) == 2

    # Verify expected columns
    assert "success" in features.columns
    assert "failed" in features.columns
    assert "agent_type" in features.columns
    assert "duration_hours" in features.columns

    # Verify success encoding
    assert features[features["name"] == "Test Cycle 1"]["success"].values[0] == 1
    assert features[features["name"] == "Test Cycle 2"]["success"].values[0] == 0


def test_extract_pdca_features_with_errors(db_session):
    """Test error count extraction."""
    user = create_test_user(db_session)

    cycle = PDCACycle(
        name="Cycle with errors",
        phase="completed",
        status="completed",
        owner_id=user.id,
        agent_type="openai"
    )
    db_session.add(cycle)
    db_session.commit()

    # Add error logs
    for i in range(3):
        log = ExecutionLog(
            cycle_id=cycle.id,
            phase="do",
            level="error",
            message=f"Error {i}"
        )
        db_session.add(log)
    db_session.commit()

    # Extract features
    features = extract_pdca_features(
        db=db_session,
        cycle_ids=[cycle.id]
    )

    # Verify error count
    assert features["error_count"].values[0] == 3
