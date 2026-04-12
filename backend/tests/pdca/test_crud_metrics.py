"""Test PDCA CRUD metrics."""
import pytest
from uuid import uuid4
from app.pdca.crud import create_pdca_cycle
from app.core.metrics import pdca_cycles_created_total


def test_create_pdca_cycle_increments_metric(db_session):
    """Test that creating a PDCA cycle increments the metric."""
    user_id = uuid4()

    # Get initial metric value
    initial_value = pdca_cycles_created_total.labels(
        user_id=str(user_id),
        department='engineering'
    )._value.get()

    # Create a PDCA cycle
    cycle_data = {
        'title': 'Test Cycle',
        'description': 'Test Description',
        'goal': 'Test Goal',
        'department': 'engineering'
    }
    create_pdca_cycle(db_session, cycle_data, user_id)

    # Check metric incremented
    final_value = pdca_cycles_created_total.labels(
        user_id=str(user_id),
        department='engineering'
    )._value.get()

    assert final_value == initial_value + 1
