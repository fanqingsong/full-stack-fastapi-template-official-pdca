"""
PDCA CRUD Operations

This module contains all CRUD operations for PDCA cycles, agent configs, and execution logs.
"""
from typing import List, Optional, Tuple
from uuid import UUID
from sqlmodel import Session, select, col
from app.pdca.models import PDCACycle, AgentConfig, ExecutionLog


# PDCA Cycle CRUD Operations

def create_pdca_cycle(session: Session, cycle_data: dict, owner_id: UUID) -> PDCACycle:
    """
    Create a new PDCA cycle.

    Args:
        session: Database session
        cycle_data: Dictionary containing cycle data (title, description, goal, etc.)
        owner_id: ID of the user who owns this cycle

    Returns:
        Created PDCACycle instance
    """
    cycle = PDCACycle(**cycle_data, owner_id=owner_id)
    session.add(cycle)
    session.commit()
    session.refresh(cycle)
    return cycle


def get_pdca_cycle(session: Session, cycle_id: UUID) -> Optional[PDCACycle]:
    """
    Get a PDCA cycle by ID.

    Args:
        session: Database session
        cycle_id: ID of the cycle to retrieve

    Returns:
        PDCACycle if found, None otherwise
    """
    statement = select(PDCACycle).where(PDCACycle.id == cycle_id)
    result = session.exec(statement).first()
    return result


def list_pdca_cycles(
    session: Session,
    owner_id: UUID,
    parent_id: Optional[UUID] = None,
    phase: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[PDCACycle], int]:
    """
    List PDCA cycles with optional filtering.

    Args:
        session: Database session
        owner_id: ID of the user to filter by
        parent_id: Optional parent cycle ID to filter child cycles
        phase: Optional phase to filter by
        status: Optional status to filter by
        skip: Number of results to skip
        limit: Maximum number of results to return

    Returns:
        Tuple of (list of PDCACycle, total count)
    """
    statement = select(PDCACycle).where(PDCACycle.owner_id == owner_id)

    if parent_id is not None:
        statement = statement.where(PDCACycle.parent_id == parent_id)
    else:
        # If no parent_id specified, only return top-level cycles
        statement = statement.where(PDCACycle.parent_id.is_(None))

    if phase is not None:
        statement = statement.where(PDCACycle.phase == phase)

    if status is not None:
        statement = statement.where(PDCACycle.status == status)

    # Get total count
    count_statement = select(col(PDCACycle.id)).where(PDCACycle.owner_id == owner_id)
    if parent_id is not None:
        count_statement = count_statement.where(PDCACycle.parent_id == parent_id)
    else:
        count_statement = count_statement.where(PDCACycle.parent_id.is_(None))
    if phase is not None:
        count_statement = count_statement.where(PDCACycle.phase == phase)
    if status is not None:
        count_statement = count_statement.where(PDCACycle.status == status)

    total_count = len(session.exec(count_statement).all())

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    statement = statement.order_by(PDCACycle.created_at.desc())

    results = session.exec(statement).all()
    return list(results), total_count


def update_pdca_cycle(session: Session, cycle: PDCACycle, cycle_update: dict) -> PDCACycle:
    """
    Update a PDCA cycle.

    Args:
        session: Database session
        cycle: PDCACycle instance to update
        cycle_update: Dictionary containing fields to update

    Returns:
        Updated PDCACycle instance
    """
    for key, value in cycle_update.items():
        setattr(cycle, key, value)

    session.add(cycle)
    session.commit()
    session.refresh(cycle)
    return cycle


def delete_pdca_cycle(session: Session, cycle: PDCACycle) -> bool:
    """
    Delete a PDCA cycle.

    Args:
        session: Database session
        cycle: PDCACycle instance to delete

    Returns:
        True if deleted successfully
    """
    session.delete(cycle)
    session.commit()
    return True


def get_child_cycles(session: Session, parent_id: UUID) -> List[PDCACycle]:
    """
    Get all child cycles of a parent cycle.

    Args:
        session: Database session
        parent_id: ID of the parent cycle

    Returns:
        List of child PDCACycle instances
    """
    statement = select(PDCACycle).where(PDCACycle.parent_id == parent_id)
    statement = statement.order_by(PDCACycle.created_at.desc())
    results = session.exec(statement).all()
    return list(results)


# Agent Config CRUD Operations

def create_agent_config(session: Session, config_data: dict, owner_id: UUID) -> AgentConfig:
    """
    Create a new agent configuration.

    Args:
        session: Database session
        config_data: Dictionary containing agent config data
        owner_id: ID of the user who owns this config

    Returns:
        Created AgentConfig instance
    """
    config = AgentConfig(**config_data, owner_id=owner_id)
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def get_agent_config(session: Session, config_id: UUID) -> Optional[AgentConfig]:
    """
    Get an agent configuration by ID.

    Args:
        session: Database session
        config_id: ID of the config to retrieve

    Returns:
        AgentConfig if found, None otherwise
    """
    statement = select(AgentConfig).where(AgentConfig.id == config_id)
    result = session.exec(statement).first()
    return result


def list_agent_configs(
    session: Session,
    owner_id: UUID,
    agent_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[AgentConfig], int]:
    """
    List agent configurations with optional filtering.

    Args:
        session: Database session
        owner_id: ID of the user to filter by
        agent_type: Optional agent type to filter by
        skip: Number of results to skip
        limit: Maximum number of results to return

    Returns:
        Tuple of (list of AgentConfig, total count)
    """
    statement = select(AgentConfig).where(AgentConfig.owner_id == owner_id)

    if agent_type is not None:
        statement = statement.where(AgentConfig.agent_type == agent_type)

    # Get total count
    count_statement = select(col(AgentConfig.id)).where(AgentConfig.owner_id == owner_id)
    if agent_type is not None:
        count_statement = count_statement.where(AgentConfig.agent_type == agent_type)

    total_count = len(session.exec(count_statement).all())

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    statement = statement.order_by(AgentConfig.created_at.desc())

    results = session.exec(statement).all()
    return list(results), total_count


# Execution Log CRUD Operations

def create_execution_log(
    session: Session,
    cycle_id: UUID,
    phase: str,
    level: str,
    message: str,
    metadata: Optional[dict] = None,
) -> ExecutionLog:
    """
    Create a new execution log entry.

    Args:
        session: Database session
        cycle_id: ID of the PDCA cycle
        phase: Phase where the log was created (plan/do/check/act)
        level: Log level (info/warning/error/debug)
        message: Log message
        metadata: Optional additional metadata

    Returns:
        Created ExecutionLog instance
    """
    log = ExecutionLog(
        cycle_id=cycle_id,
        phase=phase,
        level=level,
        message=message,
        log_metadata=metadata or {},
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def get_cycle_logs(
    session: Session,
    cycle_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[ExecutionLog]:
    """
    Get execution logs for a specific cycle.

    Args:
        session: Database session
        cycle_id: ID of the PDCA cycle
        skip: Number of results to skip
        limit: Maximum number of results to return

    Returns:
        List of ExecutionLog instances
    """
    statement = select(ExecutionLog).where(ExecutionLog.cycle_id == cycle_id)
    statement = statement.offset(skip).limit(limit)
    statement = statement.order_by(ExecutionLog.created_at.desc())
    results = session.exec(statement).all()
    return list(results)
