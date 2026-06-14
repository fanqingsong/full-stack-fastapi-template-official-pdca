"""Data models for causal inference analysis."""

import uuid
from typing import List, Dict, Any, Optional, Literal
from sqlmodel import SQLModel, Field
from datetime import datetime


class CausalQueryRequest(SQLModel):
    """Request model for causal analysis."""
    natural_language: str = Field(..., min_length=10, max_length=500)
    max_results: int = Field(default=10, ge=1, le=50)


class CausalNode(SQLModel):
    """Node in causal graph."""
    name: str
    label: str
    node_type: Literal["treatment", "outcome", "confounder", "mediator"]
    strength: float = Field(ge=0, le=1)


class CausalEdge(SQLModel):
    """Edge (causal relationship) in graph."""
    cause: str
    effect: str
    effect_size: float
    confidence: float = Field(ge=0, le=1)
    method: Literal["backdoor", "frontdoor", "iv"]


class CausalGraph(SQLModel):
    """Complete causal graph structure."""
    nodes: List[CausalNode]
    edges: List[CausalEdge]
    metadata: Dict[str, Any] = {}


class CausalAnalysisResponse(SQLModel):
    """Response from causal analysis."""
    graph: CausalGraph
    explanation: str
    statistics: Dict[str, Any]
    query_understanding: str
    analysis_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class AnalysisRequest(SQLModel):
    """Structured analysis request parsed from natural language."""
    outcome_variable: str
    treatment_variables: List[str]
    analysis_type: Literal["success_factors", "timing_drivers", "error_analysis"]
    filters: Dict[str, Any] = {}

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
        graph: "causal_graph",
        effects: Dict[str, float],
        statistics: Dict[str, Any],
        model: Any
    ):
        self.graph = graph
        self.effects = effects
        self.statistics = statistics
        self.model = model
