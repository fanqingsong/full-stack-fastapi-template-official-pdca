"""LangGraph-based PDCA workflow engine."""

import uuid
import asyncio
from typing import Dict, Any, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from sqlmodel import Session

from app.pdca.state import PDCAState
from app.pdca.agents.registry import AgentRegistry
from app.pdca.crud import (
    create_execution_log,
    get_pdca_cycle,
    get_child_cycles,
    update_pdca_cycle
)
from app.pdca.models import PDCACycleUpdate


class PDCAEngine:
    """PDCA workflow engine using LangGraph StateGraph."""

    def __init__(self, db_session: Session):
        """
        Initialize the PDCA engine.

        Args:
            db_session: Database session for CRUD operations
        """
        self.db_session = db_session
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph for PDCA workflow.

        Returns:
            Compiled StateGraph with checkpointer
        """
        # Create StateGraph with PDCAState
        workflow = StateGraph(PDCAState)

        # Add nodes for each PDCA phase
        workflow.add_node("plan_node", self._plan_node)
        workflow.add_node("do_node", self._do_node)
        workflow.add_node("check_node", self._check_node)
        workflow.add_node("act_node", self._act_node)

        # Set entry point
        workflow.set_entry_point("plan_node")

        # Add edges: plan -> do -> check
        workflow.add_edge("plan_node", "do_node")
        workflow.add_edge("do_node", "check_node")

        # Add conditional edges from check based on result
        workflow.add_conditional_edges(
            "check_node",
            self._should_continue_or_improve,
            {
                "continue": END,
                "improve": "act_node"
            }
        )

        # Add edge from act to end
        workflow.add_edge("act_node", END)

        # Compile with checkpointer
        return workflow.compile(checkpointer=self.checkpointer)

    async def _plan_node(self, state: PDCAState) -> PDCAState:
        """
        Plan phase: Set goals and plan details.

        Args:
            state: Current PDCA state

        Returns:
            Updated state with phase="plan"
        """
        # Extract cycle_id from state
        cycle_id = uuid.UUID(state["id"])

        # Create execution log (run in executor since it's sync)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: create_execution_log(
                self.db_session,
                cycle_id=cycle_id,
                phase="plan",
                level="info",
                message="Plan phase started"
            )
        )

        # Check for child cycles
        children = await loop.run_in_executor(
            None,
            lambda: self._get_children_sync(cycle_id)
        )
        has_children = len(children) > 0

        if has_children:
            await loop.run_in_executor(
                None,
                lambda: create_execution_log(
                    self.db_session,
                    cycle_id=cycle_id,
                    phase="plan",
                    level="info",
                    message=f"Waiting for {len(children)} child cycles to complete"
                )
            )

        # Update state
        state["phase"] = "plan"
        state["updated_at"] = datetime.utcnow()

        return state

    async def _do_node(self, state: PDCAState) -> PDCAState:
        """
        Do phase: Execute agent tasks.

        Args:
            state: Current PDCA state

        Returns:
            Updated state with execution results
        """
        # Extract cycle_id and agent info from state
        cycle_id = uuid.UUID(state["id"])
        agent_type = state.get("agent_type", "openai")
        agent_input = state.get("agent_input", {})

        # Create execution log (run in executor since it's sync)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: create_execution_log(
                self.db_session,
                cycle_id=cycle_id,
                phase="do",
                level="info",
                message=f"Do phase started with agent type: {agent_type}"
            )
        )

        # Get executor from registry and execute
        try:
            executor = AgentRegistry.get_executor(agent_type)
            task = agent_input.get("prompt", "")

            # Execute agent (async)
            result = await executor.execute(task, agent_input)

            # Create success log (run in executor since it's sync)
            await loop.run_in_executor(
                None,
                lambda: create_execution_log(
                    self.db_session,
                    cycle_id=cycle_id,
                    phase="do",
                    level="info",
                    message=f"Agent execution completed successfully",
                    metadata={"status": result.get("status")}
                )
            )

            # Update state with successful result
            state["execution_result"] = result
            state["error"] = None

        except Exception as e:
            # Create error log (run in executor since it's sync)
            await loop.run_in_executor(
                None,
                lambda: create_execution_log(
                    self.db_session,
                    cycle_id=cycle_id,
                    phase="do",
                    level="error",
                    message=f"Agent execution failed: {str(e)}",
                    metadata={"error": str(e)}
                )
            )

            # Update state with error
            state["execution_result"] = {
                "status": "error",
                "error": str(e)
            }
            state["error"] = str(e)

        # Update phase and timestamp
        state["phase"] = "do"
        state["updated_at"] = datetime.utcnow()

        return state

    async def _check_node(self, state: PDCAState) -> PDCAState:
        """
        Check phase: Validate execution results.

        Args:
            state: Current PDCA state

        Returns:
            Updated state with check results
        """
        cycle_id = uuid.UUID(state["id"])

        # Create execution log (run in executor since it's sync)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: create_execution_log(
                self.db_session,
                cycle_id=cycle_id,
                phase="check",
                level="info",
                message="Check phase started"
            )
        )

        # Get execution result
        execution_result = state.get("execution_result", {})

        # Check if execution was successful
        if execution_result.get("status") == "success":
            passed = True
            approval_status = "auto_approved"
        else:
            passed = False
            approval_status = "auto_rejected"

        # Create check result
        check_result = {
            "execution_status": execution_result.get("status", "unknown"),
            "passed": passed,
            "checked_at": datetime.utcnow().isoformat()
        }

        # Update state
        state["phase"] = "check"
        state["passed"] = passed
        state["check_result"] = check_result
        state["approval_status"] = approval_status
        state["updated_at"] = datetime.utcnow()

        # Create log for check result (run in executor since it's sync)
        await loop.run_in_executor(
            None,
            lambda: create_execution_log(
                self.db_session,
                cycle_id=cycle_id,
                phase="check",
                level="info",
                message=f"Check completed: passed={passed}, status={approval_status}"
            )
        )

        return state

    async def _act_node(self, state: PDCAState) -> PDCAState:
        """
        Act phase: Handle improvements when check fails.

        Args:
            state: Current PDCA state

        Returns:
            Updated state with improvement actions
        """
        cycle_id = uuid.UUID(state["id"])

        # Create execution log (run in executor since it's sync)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: create_execution_log(
                self.db_session,
                cycle_id=cycle_id,
                phase="act",
                level="info",
                message="Act phase started - implementing improvements"
            )
        )

        # Create improvement action
        improvement_actions = [
            {
                "action": "review_and_adjust",
                "description": "Review execution results and adjust parameters",
                "created_at": datetime.utcnow().isoformat()
            }
        ]

        # Update state
        state["phase"] = "act"
        state["improvement_actions"] = improvement_actions
        state["updated_at"] = datetime.utcnow()

        return state

    def _should_continue_or_improve(
        self,
        state: PDCAState
    ) -> Literal["continue", "improve"]:
        """
        Determine workflow direction after check phase.

        Args:
            state: Current PDCA state

        Returns:
            "continue" if passed and approved, "improve" otherwise
        """
        passed = state.get("passed", False)
        approval_status = state.get("approval_status", "pending")

        if passed and approval_status in ["auto_approved", "approved"]:
            return "continue"
        else:
            return "improve"

    def _get_children_sync(self, parent_id: uuid.UUID) -> list:
        """
        Get child cycles synchronously.

        Args:
            parent_id: Parent cycle ID

        Returns:
            List of child cycles
        """
        # get_child_cycles is synchronous now, just call it directly
        return get_child_cycles(self.db_session, parent_id)

    async def execute_cycle(self, cycle_id: uuid.UUID) -> PDCAState:
        """
        Execute a complete PDCA cycle.

        Args:
            cycle_id: ID of the cycle to execute

        Returns:
            Final PDCAState after execution
        """
        # Get cycle from database (run in executor since it's sync)
        loop = asyncio.get_event_loop()
        cycle = await loop.run_in_executor(
            None,
            lambda: get_pdca_cycle(self.db_session, cycle_id)
        )

        if not cycle:
            raise ValueError(f"Cycle not found: {cycle_id}")

        # Build initial PDCAState from cycle data
        initial_state: PDCAState = {
            "id": str(cycle.id),
            "parent_id": str(cycle.parent_id) if cycle.parent_id else None,
            "phase": cycle.phase or "plan",
            "goal": cycle.state_data.get("goal", "Default goal"),
            "plan_details": cycle.state_data.get("plan_details", {}),
            "agent_type": cycle.agent_type or "openai",
            "agent_input": cycle.state_data.get("agent_input", {}),
            "execution_result": None,
            "check_criteria": cycle.state_data.get("check_criteria", {}),
            "check_result": None,
            "passed": None,
            "approval_status": None,
            "improvement_actions": [],
            "created_at": cycle.created_at,
            "updated_at": cycle.updated_at,
            "error": None
        }

        # Update cycle status to running (run in executor since it's sync)
        await loop.run_in_executor(
            None,
            lambda: update_pdca_cycle(
                self.db_session,
                cycle,
                {"status": "running"}
            )
        )

        # Invoke graph with thread_id for checkpointing (async)
        config = {"configurable": {"thread_id": str(cycle_id)}}
        final_state = await self.graph.ainvoke(initial_state, config)

        # Update cycle with final phase and status (run in executor since it's sync)
        final_phase = final_state.get("phase", "plan")
        final_status = "completed" if final_state.get("passed") else "failed"

        await loop.run_in_executor(
            None,
            lambda: update_pdca_cycle(
                self.db_session,
                cycle,
                {
                    "phase": final_phase,
                    "status": final_status,
                    "state_data": final_state
                }
            )
        )

        return final_state
