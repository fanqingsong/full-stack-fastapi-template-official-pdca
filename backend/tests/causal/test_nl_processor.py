"""Tests for natural language query processing."""

import pytest
from app.causal.nl_processor import NLQueryProcessor
from app.causal.models import AnalysisRequest


@pytest.mark.no_db
def test_extract_success_analysis_request():
    """Test parsing success-related query."""
    processor = NLQueryProcessor()

    query = "What causes my PDCA cycles to succeed?"
    request = processor.extract_analysis_request(
        query=query,
        available_vars=["success", "agent_type", "duration_hours"]
    )

    assert isinstance(request, AnalysisRequest)
    assert request.outcome_variable == "success"
    assert len(request.treatment_variables) > 0
    assert request.analysis_type == "success_factors"


@pytest.mark.no_db
def test_extract_timing_analysis_request():
    """Test parsing timing-related query."""
    processor = NLQueryProcessor()

    query = "What factors lead to longer execution times?"
    request = processor.extract_analysis_request(
        query=query,
        available_vars=["duration_hours", "agent_type", "error_count"]
    )

    assert request.outcome_variable == "duration_hours"
    assert request.analysis_type == "timing_drivers"


@pytest.mark.no_db
def test_extract_error_analysis_request():
    """Test parsing error-related query."""
    processor = NLQueryProcessor()

    query = "Why do my cycles fail in the Check phase?"
    request = processor.extract_analysis_request(
        query=query,
        available_vars=["failed", "error_count", "agent_type"]
    )

    assert request.outcome_variable in ["failed", "error_count"]
    assert request.analysis_type == "error_analysis"
