"""Test data factories for causal analysis."""

import pandas as pd
import numpy as np
from typing import List, Tuple


def generate_synthetic_data(
    n: int = 1000,
    structure: List[Tuple[str, str, float]] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic data with known causal structure.

    Args:
        n: Number of samples
        structure: List of (cause, effect, strength) tuples
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic data
    """
    np.random.seed(seed)

    if structure is None:
        # Default structure: X -> Y <- Z
        structure = [("X", "Y", 0.5), ("Z", "Y", 0.3)]

    # Get all unique variables
    variables = set()
    for cause, effect, _ in structure:
        variables.add(cause)
        variables.add(effect)

    # Generate root variables (those that are only causes)
    data = {}
    for var in variables:
        is_root = not any(var == effect for _, effect, _ in structure)
        if is_root:
            data[var] = np.random.randn(n)

    # Generate effect variables based on causes
    for cause, effect, strength in structure:
        if effect not in data:
            # First time seeing this effect
            data[effect] = strength * data[cause] + 0.5 * np.random.randn(n)
        else:
            # Effect already exists, add this cause
            data[effect] += strength * data[cause]

    return pd.DataFrame(data)


def create_pdca_cycle_data(
    n_success: int = 70,
    n_failure: int = 30
) -> pd.DataFrame:
    """
    Create synthetic PDCA cycle data for testing.

    Returns DataFrame with columns:
    - success: binary outcome
    - agent_type: categorical treatment
    - duration_hours: continuous outcome
    - error_count: count outcome
    """
    np.random.seed(42)

    data = []

    # Successful cycles
    for _ in range(n_success):
        data.append({
            "success": 1,
            "failed": 0,
            "agent_type": np.random.choice(["openai", "python_script"]),
            "duration_hours": np.random.uniform(1, 5),
            "error_count": np.random.poisson(1),
            "has_parent": np.random.choice([0, 1]),
            "created_hour": np.random.randint(0, 24),
        })

    # Failed cycles
    for _ in range(n_failure):
        data.append({
            "success": 0,
            "failed": 1,
            "agent_type": np.random.choice(["python_script", "shell_command"]),
            "duration_hours": np.random.uniform(5, 15),
            "error_count": np.random.poisson(5),
            "has_parent": np.random.choice([0, 1]),
            "created_hour": np.random.randint(0, 24),
        })

    return pd.DataFrame(data)
