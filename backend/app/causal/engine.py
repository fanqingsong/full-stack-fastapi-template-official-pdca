"""Main causal analysis engine using causal-learn."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from causallearn.search.ConstraintBased.PC import pc
from causallearn.utils.GraphUtils import GraphUtils

from app.causal.models import CausalGraph, CausalNode, CausalEdge
from app.causal.exceptions import InsufficientDataError, UnidentifiableEffectError


class CausalEngine:
    """Main causal analysis engine using causal-learn."""

    def __init__(self, alpha: float = 0.05):
        """
        Initialize causal engine.

        Args:
            alpha: Significance level for independence tests (default 0.05)
        """
        self.alpha = alpha

    def analyze_causal_relationships(
        self,
        data: pd.DataFrame,
        treatment_vars: list[str],
        outcome_var: str,
        algorithm: str = "pc"
    ) -> 'CausalResult':
        """
        Discover and analyze causal relationships.

        Args:
            data: Input DataFrame
            treatment_vars: Potential treatment variables
            outcome_var: Outcome variable
            algorithm: Causal discovery algorithm ('pc', 'fci')

        Returns:
            CausalResult with graph, effects, and statistics

        Raises:
            InsufficientDataError: Not enough data for reliable analysis
            UnidentifiableEffectError: Causal effect cannot be identified
        """
        # Validate data
        self._validate_data(data, treatment_vars, outcome_var)

        # Preprocess data
        processed_data = self._preprocess_data(data, treatment_vars + [outcome_var])

        # Discover causal structure
        causal_graph = self._discover_structure(processed_data, algorithm)

        # Estimate causal effects
        effects = self._estimate_effects(
            processed_data, causal_graph, treatment_vars, outcome_var
        )

        # Build statistics
        statistics = self._build_statistics(
            processed_data, causal_graph, effects
        )

        return CausalResult(
            graph=causal_graph,
            effects=effects,
            statistics=statistics,
            model=None
        )

    def _validate_data(
        self,
        data: pd.DataFrame,
        treatment_vars: list[str],
        outcome_var: str
    ):
        """Validate input data."""
        if len(data) < 50:
            raise InsufficientDataError(len(data), 50)

        required_vars = treatment_vars + [outcome_var]
        missing_vars = [var for var in required_vars if var not in data.columns]
        if missing_vars:
            raise ValueError(f"Missing variables: {missing_vars}")

        if data[required_vars].isnull().any().any():
            raise ValueError("Data contains missing values")

    def _preprocess_data(
        self,
        data: pd.DataFrame,
        variables: list[str]
    ) -> np.ndarray:
        """Preprocess data for causal discovery."""
        # Select relevant columns
        subset = data[variables].copy()

        # Convert categorical to numeric
        for col in subset.select_dtypes(include=['object']).columns:
            subset[col] = pd.factorize(subset[col])[0]

        return subset.values

    def _discover_structure(
        self,
        data: np.ndarray,
        algorithm: str
    ) -> CausalGraph:
        """Discover causal graph structure."""
        if algorithm == "pc":
            # PC algorithm (constraint-based)
            cg = pc(data, alpha=self.alpha, indep_test='fisherz')

            # Convert to our graph format
            return self._convert_causallearn_graph(cg, data.shape[1])
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def _convert_causallearn_graph(
        self,
        cg_graph,
        num_vars: int
    ) -> CausalGraph:
        """Convert causal-learn graph to our format."""
        # Get graph labels
        labels = [f"X{i}" for i in range(num_vars)]

        # Extract nodes and edges
        nodes = []
        edges = []

        # Add nodes
        for i, label in enumerate(labels):
            nodes.append(CausalNode(
                name=label,
                label=label,
                node_type="treatment",  # Default, will be refined
                strength=0.5
            ))

        # Extract edges from graph
        # (This is simplified - real implementation would parse cg_graph.G)
        for i in range(num_vars):
            for j in range(num_vars):
                if i != j:
                    # Add placeholder edge (real impl would check graph structure)
                    edges.append(CausalEdge(
                        cause=f"X{i}",
                        effect=f"X{j}",
                        effect_size=0.3,
                        confidence=0.95,
                        method="backdoor"
                    ))

        return CausalGraph(nodes=nodes, edges=edges)

    def _estimate_effects(
        self,
        data: np.ndarray,
        graph: CausalGraph,
        treatment_vars: list[str],
        outcome_var: str
    ) -> dict[str, float]:
        """Estimate causal effects."""
        # Simplified implementation using correlation
        effects = {}

        for treatment in treatment_vars:
            # Get indices
            try:
                t_idx = list(graph.nodes).index(treatment)
                o_idx = list(graph.nodes).index(outcome_var)
            except ValueError:
                continue

            # Calculate correlation as effect estimate
            correlation = np.corrcoef(data[:, t_idx], data[:, o_idx])[0, 1]
            effects[treatment] = abs(correlation)

        return effects

    def _build_statistics(
        self,
        data: np.ndarray,
        graph: CausalGraph,
        effects: dict[str, float]
    ) -> dict[str, Any]:
        """Build analysis statistics."""
        return {
            "sample_size": len(data),
            "algorithm": "pc",
            "num_variables": len(graph.nodes),
            "num_edges": len(graph.edges),
            "significant_effects": len([e for e in effects.values() if e > 0.1])
        }


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
