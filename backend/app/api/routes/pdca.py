"""PDCA API routes for managing PDCA cycles and agent configurations."""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import SessionDep, CurrentUser
from app.models import User
from app.pdca.models import (
    PDCACycle,
    PDCACycleCreate,
    PDCACycleUpdate,
    PDCACyclePublic,
    PDCACyclesPublic,
    AgentConfig,
    AgentConfigCreate,
    AgentConfigPublic,
    AgentConfigsPublic
)
from app.pdca.crud import (
    create_pdca_cycle,
    get_pdca_cycle,
    list_pdca_cycles,
    update_pdca_cycle,
    delete_pdca_cycle,
    get_child_cycles,
    create_agent_config,
    get_agent_config,
    list_agent_configs,
    get_cycle_logs
)
from app.pdca.engine import PDCAEngine
from app.pdca.agents.registry import AgentRegistry

router = APIRouter(prefix="/pdca", tags=["PDCA"])


# PDCA Cycle Endpoints

@router.post("/cycles", response_model=PDCACyclePublic, status_code=status.HTTP_201_CREATED)
def create_cycle(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    cycle_data: PDCACycleCreate
) -> PDCACycle:
    """
    Create a new PDCA cycle.

    Args:
        session: Database session
        current_user: Authenticated user
        cycle_data: PDCA cycle creation data

    Returns:
        Created PDCA cycle
    """
    cycle = create_pdca_cycle(session, cycle_data.model_dump(), current_user.id)
    return cycle


@router.get("/cycles", response_model=PDCACyclesPublic)
def read_cycles(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    parent_id: Optional[UUID] = None,
    phase: Optional[str] = None,
    status_param: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> PDCACyclesPublic:
    """
    List PDCA cycles with optional filtering.

    Args:
        session: Database session
        current_user: Authenticated user
        parent_id: Optional parent cycle ID filter
        phase: Optional phase filter
        status_param: Optional status filter
        skip: Number of results to skip
        limit: Maximum number of results

    Returns:
        List of PDCA cycles with count
    """
    cycles, count = list_pdca_cycles(
        session,
        owner_id=current_user.id,
        parent_id=parent_id,
        phase=phase,
        status=status_param,
        skip=skip,
        limit=limit
    )
    return PDCACyclesPublic(data=cycles, count=count)


@router.get("/cycles/{cycle_id}", response_model=PDCACyclePublic)
def read_cycle(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: UUID
) -> PDCACycle:
    """
    Get a single PDCA cycle by ID.

    Args:
        session: Database session
        current_user: Authenticated user
        cycle_id: PDCA cycle ID

    Returns:
        PDCA cycle

    Raises:
        404: If cycle not found
        403: If user doesn't own the cycle
    """
    cycle = get_pdca_cycle(session, cycle_id)
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDCA cycle not found"
        )
    if cycle.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return cycle


@router.post("/cycles/{cycle_id}/execute", response_model=PDCACyclePublic)
async def execute_cycle(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: UUID
) -> PDCACycle:
    """
    Execute a PDCA cycle asynchronously.

    Args:
        session: Database session
        current_user: Authenticated user
        cycle_id: PDCA cycle ID to execute

    Returns:
        Updated PDCA cycle after execution

    Raises:
        404: If cycle not found
        403: If user doesn't own the cycle
        500: If execution fails
    """
    cycle = get_pdca_cycle(session, cycle_id)
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDCA cycle not found"
        )
    if cycle.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    try:
        engine = PDCAEngine(session)
        await engine.execute_cycle(cycle_id)
        # Re-fetch cycle to get updated state
        session.expire_all()
        cycle = get_pdca_cycle(session, cycle_id)
        return cycle
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )


@router.get("/cycles/{cycle_id}/children", response_model=PDCACyclesPublic)
def read_child_cycles(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: UUID
) -> PDCACyclesPublic:
    """
    Get all child cycles of a parent PDCA cycle.

    Args:
        session: Database session
        current_user: Authenticated user
        cycle_id: Parent PDCA cycle ID

    Returns:
        List of child PDCA cycles

    Raises:
        404: If parent cycle not found
        403: If user doesn't own the parent cycle
    """
    parent_cycle = get_pdca_cycle(session, cycle_id)
    if not parent_cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent PDCA cycle not found"
        )
    if parent_cycle.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    children = get_child_cycles(session, cycle_id)
    return PDCACyclesPublic(data=children, count=len(children))


@router.delete("/cycles/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cycle(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    cycle_id: UUID
) -> None:
    """
    Delete a PDCA cycle.

    Args:
        session: Database session
        current_user: Authenticated user
        cycle_id: PDCA cycle ID to delete

    Raises:
        404: If cycle not found
        403: If user doesn't own the cycle
    """
    cycle = get_pdca_cycle(session, cycle_id)
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDCA cycle not found"
        )
    if cycle.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    delete_pdca_cycle(session, cycle)


# Agent Config Endpoints

@router.post("/agents/configs", response_model=AgentConfigPublic, status_code=status.HTTP_201_CREATED)
def create_agent_config_route(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    config_data: AgentConfigCreate
) -> AgentConfig:
    """
    Create a new agent configuration.

    Args:
        session: Database session
        current_user: Authenticated user
        config_data: Agent configuration data

    Returns:
        Created agent configuration
    """
    config = create_agent_config(session, config_data.model_dump(), current_user.id)
    return config


@router.get("/agents/configs", response_model=AgentConfigsPublic)
def read_agent_configs(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> AgentConfigsPublic:
    """
    List agent configurations with optional filtering.

    Args:
        session: Database session
        current_user: Authenticated user
        agent_type: Optional agent type filter
        skip: Number of results to skip
        limit: Maximum number of results

    Returns:
        List of agent configurations with count
    """
    configs, count = list_agent_configs(
        session,
        owner_id=current_user.id,
        agent_type=agent_type,
        skip=skip,
        limit=limit
    )
    return AgentConfigsPublic(data=configs, count=count)


@router.get("/agents/types")
def list_agent_types() -> dict[str, list[str]]:
    """
    List all available agent types.

    Returns:
        Dictionary with list of registered agent types
    """
    types = AgentRegistry.list_types()
    return {"types": types}
