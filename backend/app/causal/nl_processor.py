"""Natural language query processing for causal analysis."""

import json
import re
from typing import List, Dict, Any, Optional
from pydantic import ValidationError

from app.causal.models import AnalysisRequest
from app.causal.exceptions import QueryAmbiguityError


class NLQueryProcessor:
    """Process natural language queries using regex patterns."""

    def __init__(self):
        """Initialize NL query processor."""
        self.patterns = self._compile_patterns()

    def extract_analysis_request(
        self,
        query: str,
        available_vars: List[str]
    ) -> AnalysisRequest:
        """
        Parse natural language query into structured analysis request.

        Args:
            query: Natural language query from user
            available_vars: List of available variables

        Returns:
            AnalysisRequest with parsed parameters

        Raises:
            QueryAmbiguityError: If query is too ambiguous
        """
        # Normalize query
        query_lower = query.lower().strip()

        # Determine analysis type
        analysis_type = self._determine_analysis_type(query_lower)

        # Extract outcome variable
        outcome_var = self._extract_outcome_variable(
            query_lower,
            available_vars,
            analysis_type
        )

        # Extract treatment variables
        treatment_vars = self._extract_treatment_variables(
            query_lower,
            available_vars,
            outcome_var
        )

        # Extract filters
        filters = self._extract_filters(query_lower)

        if not outcome_var:
            raise QueryAmbiguityError(
                query,
                ["Could not identify outcome variable"]
            )

        return AnalysisRequest(
            outcome_variable=outcome_var,
            treatment_variables=treatment_vars,
            analysis_type=analysis_type,
            filters=filters
        )

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for query parsing."""
        return {
            "success": [
                re.compile(r"succeed|success|complete|work")
            ],
            "failure": [
                re.compile(r"fail|error|broken|crash")
            ],
            "timing": [
                re.compile(r"duration|time|slow|fast|long|short")
            ],
            "causation": [
                re.compile(r"cause|affect|impact|influence|drive|lead to")
            ]
        }

    def _determine_analysis_type(self, query: str) -> str:
        """Determine the type of analysis from query."""
        if any(p.search(query) for p in self.patterns["success"]):
            return "success_factors"
        elif any(p.search(query) for p in self.patterns["timing"]):
            return "timing_drivers"
        elif any(p.search(query) for p in self.patterns["failure"]):
            return "error_analysis"
        else:
            return "success_factors"  # Default

    def _extract_outcome_variable(
        self,
        query: str,
        available_vars: List[str],
        analysis_type: str
    ) -> Optional[str]:
        """Extract outcome variable from query."""
        # Map analysis types to default outcomes
        type_to_outcome = {
            "success_factors": "success",
            "timing_drivers": "duration_hours",
            "error_analysis": "error_count"
        }

        default_outcome = type_to_outcome.get(analysis_type, "success")

        # Check if default is available
        if default_outcome in available_vars:
            return default_outcome

        # Fallback to first available variable
        for var in available_vars:
            if any(word in var for word in query.split()):
                return var

        return available_vars[0] if available_vars else None

    def _extract_treatment_variables(
        self,
        query: str,
        available_vars: List[str],
        outcome_var: str
    ) -> List[str]:
        """Extract treatment variables from query."""
        # Exclude outcome variable
        potential_treatments = [v for v in available_vars if v != outcome_var]

        # Return all potential treatments (will be refined by analysis)
        return potential_treatments

    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract filters from query (placeholder for MVP)."""
        # MVP: No complex filtering
        return {}
