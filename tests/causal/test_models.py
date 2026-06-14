"""Tests for causal data models."""

import pytest
from app.causal.models import (
    CausalQueryRequest,
    CausalNode,
    CausalEdge,
    CausalGraph,
    CausalAnalysisResponse,
    AnalysisRequest,
)


def test_causal_query_request_validation():
    """Test query request validation."""
    # Valid request
    request = CausalQueryRequest(
        natural_language="What causes my cycles to succeed?"
    )
    assert request.natural_language == "What causes my cycles to succeed?"
    assert request.max_results == 10

    # Too short
    with pytest.raises(ValueError):
        CausalQueryRequest(natural_language="Too short")

    # Invalid max_results
    with pytest.raises(ValueError):
        CausalQueryRequest(
            natural_language="Valid query length here",
            max_results=100
        )


def test_causal_node_model():
    """Test causal node model."""
    node = CausalNode(
        name="agent_type",
        label="Agent Type",
        node_type="treatment",
        strength=0.75
    )
    assert node.name == "agent_type"
    assert node.node_type == "treatment"
    assert 0 <= node.strength <= 1


def test_causal_edge_model():
    """Test causal edge model."""
    edge = CausalEdge(
        cause="agent_type",
        effect="success",
        effect_size=0.35,
        confidence=0.95,
        method="backdoor"
    )
    assert edge.cause == "agent_type"
    assert edge.effect == "success"
    assert edge.method == "backdoor"


def test_analysis_request_summary():
    """Test analysis request summary generation."""
    request = AnalysisRequest(
        outcome_variable="success",
        treatment_variables=["agent_type", "duration", "has_parent"],
        analysis_type="success_factors"
    )

    summary = request.summary()
    assert "success" in summary
    assert "agent_type" in summary


def test_causal_graph_structure():
    """Test causal graph structure."""
    graph = CausalGraph(
        nodes=[
            CausalNode(name="X", label="X", node_type="treatment", strength=0.8),
            CausalNode(name="Y", label="Y", node_type="outcome", strength=0.5)
        ],
        edges=[
            CausalEdge(cause="X", effect="Y", effect_size=0.5, confidence=0.95, method="backdoor")
        ]
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].cause == "X"
    assert graph.edges[0].effect == "Y"
