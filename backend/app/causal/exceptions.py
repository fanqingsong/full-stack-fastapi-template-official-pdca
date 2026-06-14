"""Custom exceptions for causal analysis."""

from typing import List


class CausalAnalysisError(Exception):
    """Base exception for causal analysis errors."""
    pass


class InsufficientDataError(CausalAnalysisError):
    """Raised when not enough data for reliable analysis."""
    def __init__(self, sample_size: int, required: int = 50):
        self.sample_size = sample_size
        self.required = required
        super().__init__(
            f"Insufficient data: {sample_size} samples, need at least {required}"
        )


class UnidentifiableEffectError(CausalAnalysisError):
    """Raised when causal effect cannot be identified."""
    def __init__(self, reason: str):
        super().__init__(f"Causal effect cannot be identified: {reason}")


class QueryAmbiguityError(CausalAnalysisError):
    """Raised when natural language query is too ambiguous."""
    def __init__(self, query: str, ambiguities: List[str]):
        self.ambiguities = ambiguities
        super().__init__(
            f"Query '{query}' is ambiguous. Please clarify: {', '.join(ambiguities)}"
        )


class DataQualityError(CausalAnalysisError):
    """Raised when data has quality issues."""
    def __init__(self, issues: List[str]):
        self.issues = issues
        super().__init__(f"Data quality issues: {', '.join(issues)}")
