"""PDCA utility functions."""

from typing import Dict, Any, List
from uuid import UUID


def extract_execution_summary(execution_result: Dict[str, Any]) -> str:
    """Extract a summary from execution result.

    Args:
        execution_result: Dictionary containing execution result with status and output/error

    Returns:
        String summary of the execution result
    """
    if not execution_result:
        return "No execution result"

    status = execution_result.get("status")

    if status == "success":
        output = execution_result.get("output", "")
        # Truncate to 200 characters
        if len(output) > 200:
            return f"Success: {output[:200]}..."
        return f"Success: {output}..."
    elif status == "error":
        error = execution_result.get("error", "Unknown error")
        return f"Error: {error}"
    else:
        return "No execution result"


def calculate_cycle_progress(state_data: Dict[str, Any]) -> float:
    """Calculate progress percentage based on cycle phase.

    Args:
        state_data: Dictionary containing cycle state data with 'phase' field

    Returns:
        Progress percentage (0-100)
    """
    phase = state_data.get("phase", "plan")

    progress_map = {
        "plan": 25,
        "do": 50,
        "check": 75,
        "act": 90,
        "completed": 100,
        "failed": 100,
    }

    return progress_map.get(phase, 0)


def validate_agent_input(agent_type: str, input_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate agent input based on agent type.

    Args:
        agent_type: Type of agent (e.g., "openai", "http_request")
        input_data: Dictionary containing input data for the agent

    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors: List[str] = []

    if agent_type == "openai":
        if "prompt" not in input_data:
            errors.append("Missing required field: prompt")
    elif agent_type == "http_request":
        if "url" not in input_data:
            errors.append("Missing required field: url")
        if "method" not in input_data:
            errors.append("Missing required field: method")

    return (len(errors) == 0, errors)


def format_cycle_tree(cycles: List[Any]) -> List[Dict[str, Any]]:
    """Format cycles into a tree structure with parent-child relationships.

    Args:
        cycles: List of PDCACycle objects

    Returns:
        List of root cycle dictionaries with nested children
    """
    # Build ID to cycle mapping
    cycle_map: Dict[str, Any] = {}
    for cycle in cycles:
        cycle_map[str(cycle.id)] = cycle

    # Find root cycles (parent_id is None)
    roots = [cycle for cycle in cycles if cycle.parent_id is None]

    # Recursively build tree structure
    tree = []
    for root in roots:
        tree.append(_build_tree_node(root, cycle_map))

    return tree


def _build_tree_node(cycle: Any, cycle_map: Dict[str, Any]) -> Dict[str, Any]:
    """Build a tree node for a cycle with its children.

    Args:
        cycle: PDCACycle object
        cycle_map: Dictionary mapping cycle IDs to cycle objects

    Returns:
        Dictionary representing the tree node
    """
    # Find children where child.parent_id == cycle.id
    children = []
    for other_cycle in cycle_map.values():
        if other_cycle.parent_id is not None and str(other_cycle.parent_id) == str(cycle.id):
            children.append(_build_tree_node(other_cycle, cycle_map))

    return {
        "id": str(cycle.id),
        "name": cycle.name,
        "phase": cycle.phase,
        "status": cycle.status,
        "children": children,
    }
