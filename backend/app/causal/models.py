"""Data models for causal inference analysis."""

import uuid
from typing import Any, Literal
from sqlmodel import SQLModel, Field


class CausalQueryRequest(SQLModel):
    """Request model for causal analysis."""
    natural_language: str = Field(..., min_length=10, max_length=500)
    max_results: int = Field(default=10, ge=1, le=50)


class CausalNode(SQLModel):
    """Node in causal graph."""

    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    node_type: Literal["treatment", "outcome", "confounder", "mediator"]
    strength: float = Field(ge=0, le=1)


class CausalEdge(SQLModel):
    """Edge (causal relationship) in graph."""

    cause: str = Field(..., max_length=100)
    effect: str = Field(..., max_length=100)
    effect_size: float
    confidence: float = Field(ge=0, le=1)
    method: Literal["backdoor", "frontdoor", "iv"]


class CausalGraph(SQLModel):
    """Complete causal graph structure."""

    nodes: list[CausalNode]
    edges: list[CausalEdge]
    graph_metadata: dict[str, Any] = Field(default_factory=dict)


class CausalAnalysisResponse(SQLModel):
    """Response from causal analysis."""

    graph: CausalGraph
    explanation: str = Field(..., max_length=2000)
    statistics: dict[str, Any]
    query_understanding: str = Field(..., max_length=500)
    analysis_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class AnalysisRequest(SQLModel):
    """Structured analysis request parsed from natural language."""

    outcome_variable: str
    treatment_variables: list[str]
    analysis_type: Literal["success_factors", "timing_drivers", "error_analysis"]
    filters: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> str:
        treatments = ", ".join(self.treatment_variables[:3])
        if len(self.treatment_variables) > 3:
            treatments += f", and {len(self.treatment_variables) - 3} others"
        return f"Analyzing how {treatments} affect {self.outcome_variable}"


# Internal models (not exposed in API)
class CausalResult:
    """Internal result from causal engine."""

    def __init__(
        self,
        graph: CausalGraph,
        effects: dict[str, float],
        statistics: dict[str, Any],
        model: Any
    ):
        self.graph = graph
        self.effects = effects
        self.statistics = statistics
        self.model = model
