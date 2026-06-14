"""Tests for causal analysis engine."""

import pytest
import pandas as pd
import numpy as np
from app.causal.engine import CausalEngine
from app.causal.exceptions import InsufficientDataError
from tests.factories import generate_synthetic_data


pytestmark = pytest.mark.no_db


def test_causal_discovery_with_known_structure():
    """Test causal discovery with synthetic ground truth."""
    # Generate data with known structure: X -> Y <- Z
    data = generate_synthetic_data(
        n=1000,
        structure=[
            ("X", "Y", 0.5),
            ("Z", "Y", 0.3)
        ]
    )

    engine = CausalEngine()
    result = engine.analyze_causal_relationships(
        data=data,
        treatment_vars=["X", "Z"],
        outcome_var="Y"
    )

    # Should discover causal relationships
    assert result.graph is not None
    assert len(result.graph.edges) >= 1

    # Should include statistics
    assert result.statistics is not None
    assert "sample_size" in result.statistics


def test_insufficient_data_error():
    """Test error handling for small datasets."""
    small_data = generate_synthetic_data(n=20)

    engine = CausalEngine()
    with pytest.raises(InsufficientDataError) as exc_info:
        engine.analyze_causal_relationships(
            data=small_data,
            treatment_vars=["X"],
            outcome_var="Y"
        )

    assert exc_info.value.sample_size == 20
    assert exc_info.value.required == 50


def test_effect_estimation():
    """Test causal effect estimation."""
    data = generate_synthetic_data(
        n=1000,
        structure=[("X", "Y", 0.5)]
    )

    engine = CausalEngine()
    result = engine.analyze_causal_relationships(
        data=data,
        treatment_vars=["X"],
        outcome_var="Y"
    )

    # Effect should be positive and significant
    assert any(
        edge.cause == "X" and edge.effect == "Y" and edge.effect_size > 0
        for edge in result.graph.edges
    )
