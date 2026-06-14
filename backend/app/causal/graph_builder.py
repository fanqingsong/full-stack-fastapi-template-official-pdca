"""Graph formatting for visualization."""

from typing import Dict, Any
from app.causal.models import CausalResult, CausalGraph


def build_graph_response(graph: CausalGraph) -> CausalGraph:
    """
    Build graph response for API.

    Args:
        graph: Internal causal graph

    Returns:
        Formatted graph for visualization
    """
    # For MVP, return as-is
    # Future: Add formatting, simplification, etc.
    return graph


async def generate_explanation(
    result: CausalResult,
    original_query: str,
    user=None
) -> str:
    """
    Generate natural language explanation of results.

    Args:
        result: Causal analysis result
        original_query: User's original query
        user: Optional user context

    Returns:
        Natural language explanation
    """
    sample_size = result.statistics.get("sample_size", 0)
    num_edges = len(result.graph.edges)

    explanation = f"""Based on analysis of {sample_size} PDCA cycles, I found {num_edges} key causal relationships.

"""

    # Add key findings
    for edge in result.graph.edges[:3]:  # Top 3 relationships
        direction = "increases" if edge.effect_size > 0 else "decreases"
        explanation += f"- {edge.cause} {direction} {edge.effect} (confidence: {edge.confidence:.2%})\n"

    explanation += f"\nThese findings suggest actionable insights to optimize your PDCA workflows."

    return explanation
