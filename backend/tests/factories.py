"""Factory functions for generating test data."""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional


def generate_synthetic_data(
    n: int = 1000,
    structure: Optional[List[Tuple[str, str, float]]] = None,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic data with known causal structure.

    Args:
        n: Number of samples to generate
        structure: List of tuples (cause, effect, strength) defining edges
                  Default: [("X", "Y", 0.5)]
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic data following the specified structure
    """
    if seed is not None:
        np.random.seed(seed)

    if structure is None:
        structure = [("X", "Y", 0.5)]

    # Collect all unique variables
    variables = set()
    for cause, effect, _ in structure:
        variables.add(cause)
        variables.add(effect)

    variables = sorted(list(variables))
    data = {}

    # Generate root variables (no parents)
    has_parent = set()
    for cause, effect, _ in structure:
        has_parent.add(effect)

    for var in variables:
        if var not in has_parent:
            # Root variable - random normal
            data[var] = np.random.randn(n)

    # Generate child variables based on parents
    # Process in topological order
    max_iterations = len(variables)
    iteration = 0

    while len(data) < len(variables) and iteration < max_iterations:
        iteration += 1
        for var in variables:
            if var in data:
                continue  # Already generated

            # Find parents
            parents = [(cause, strength) for cause, effect, strength in structure if effect == var]

            if parents and all(cause in data for cause, _ in parents):
                # Generate based on parents
                value = np.random.randn(n) * 0.1  # Noise term

                for cause, strength in parents:
                    value += strength * data[cause]

                data[var] = value

    # Add any remaining variables (shouldn't happen with valid structure)
    for var in variables:
        if var not in data:
            data[var] = np.random.randn(n)

    return pd.DataFrame(data)
