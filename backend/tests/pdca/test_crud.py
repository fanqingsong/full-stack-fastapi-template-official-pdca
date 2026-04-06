"""
Tests for PDCA CRUD operations
"""
import pytest
from sqlmodel import Session
from app.pdca.models import PDCACycle, AgentConfig, ExecutionLog
from app.pdca import crud
from app.models import User


class TestPDCAycleCRUD:
    """Test PDCA Cycle CRUD operations"""

    def test_create_pdca_cycle(self, db: Session, test_user: User) -> None:
        """Test creating a PDCA cycle"""
        cycle_data = {
            "name": "Test Cycle",
            "goal": "Test goal",
            "agent_type": "openai",
            "agent_input": {"prompt": "test prompt"},
        }

        cycle = crud.create_pdca_cycle(db, cycle_data, test_user.id)

        assert cycle is not None
        assert cycle.id is not None
        assert cycle.name == "Test Cycle"
        assert cycle.goal == "Test goal"
        assert cycle.owner_id == test_user.id
        assert cycle.phase == "plan"
        assert cycle.status == "pending"

    def test_get_pdca_cycle(self, db: Session, test_pdca_cycle: PDCACycle) -> None:
        """Test getting a PDCA cycle by ID"""
        retrieved_cycle = crud.get_pdca_cycle(db, test_pdca_cycle.id)

        assert retrieved_cycle is not None
        assert retrieved_cycle.id == test_pdca_cycle.id
        assert retrieved_cycle.name == test_pdca_cycle.name

    def test_list_pdca_cycles(self, db: Session, test_user: User, test_pdca_cycle: PDCACycle) -> None:
        """Test listing PDCA cycles"""
        # Create another cycle for the same user
        cycle_data = {
            "name": "Another Cycle",
            "goal": "Another goal",
            "agent_type": "openai",
            "agent_input": {"prompt": "another test"},
        }
        crud.create_pdca_cycle(db, cycle_data, test_user.id)

        # List all cycles
        cycles, count = crud.list_pdca_cycles(db, test_user.id)

        assert len(cycles) >= 2
        assert count >= 2
        assert all(cycle.owner_id == test_user.id for cycle in cycles)

    def test_list_pdca_cycles_with_filters(self, db: Session, test_user: User) -> None:
        """Test listing PDCA cycles with filters"""
        # Create cycles with different phases and statuses
        cycle1 = crud.create_pdca_cycle(
            db,
            {"name": "Cycle 1", "goal": "Goal 1", "agent_type": "openai", "agent_input": {}},
            test_user.id
        )
        cycle1.phase = "do"
        cycle1.status = "running"
        db.add(cycle1)
        db.commit()

        cycle2 = crud.create_pdca_cycle(
            db,
            {"name": "Cycle 2", "goal": "Goal 2", "agent_type": "openai", "agent_input": {}},
            test_user.id
        )
        cycle2.phase = "plan"
        cycle2.status = "completed"
        db.add(cycle2)
        db.commit()

        # Filter by phase
        do_cycles, do_count = crud.list_pdca_cycles(db, test_user.id, phase="do")
        assert all(c.phase == "do" for c in do_cycles)

        # Filter by status
        running_cycles, running_count = crud.list_pdca_cycles(db, test_user.id, status="running")
        assert all(c.status == "running" for c in running_cycles)

    def test_update_pdca_cycle(self, db: Session, test_pdca_cycle: PDCACycle) -> None:
        """Test updating a PDCA cycle"""
        update_data = {
            "name": "Updated Cycle",
            "phase": "do",
            "status": "running",
        }

        updated_cycle = crud.update_pdca_cycle(db, test_pdca_cycle, update_data)

        assert updated_cycle.name == "Updated Cycle"
        assert updated_cycle.phase == "do"
        assert updated_cycle.status == "running"

    def test_delete_pdca_cycle(self, db: Session, test_user: User) -> None:
        """Test deleting a PDCA cycle"""
        # Create a cycle to delete
        cycle_data = {
            "name": "To Delete",
            "goal": "Will be deleted",
            "agent_type": "openai",
            "agent_input": {},
        }
        cycle = crud.create_pdca_cycle(db, cycle_data, test_user.id)
        cycle_id = cycle.id

        # Delete the cycle
        result = crud.delete_pdca_cycle(db, cycle)

        assert result is True

        # Verify it's deleted
        deleted_cycle = crud.get_pdca_cycle(db, cycle_id)
        assert deleted_cycle is None

    def test_get_child_cycles(self, db: Session, test_user: User) -> None:
        """Test getting child cycles of a parent cycle"""
        # Create parent cycle
        parent_data = {
            "name": "Parent Cycle",
            "goal": "Parent goal",
            "agent_type": "openai",
            "agent_input": {},
        }
        parent = crud.create_pdca_cycle(db, parent_data, test_user.id)

        # Create child cycles
        child1_data = {
            "name": "Child 1",
            "goal": "Child goal 1",
            "agent_type": "openai",
            "agent_input": {},
            "parent_id": parent.id,
        }
        child1 = crud.create_pdca_cycle(db, child1_data, test_user.id)

        child2_data = {
            "name": "Child 2",
            "goal": "Child goal 2",
            "agent_type": "openai",
            "agent_input": {},
            "parent_id": parent.id,
        }
        child2 = crud.create_pdca_cycle(db, child2_data, test_user.id)

        # Get child cycles
        children = crud.get_child_cycles(db, parent.id)

        assert len(children) == 2
        assert all(c.parent_id == parent.id for c in children)
        child_names = [c.name for c in children]
        assert "Child 1" in child_names
        assert "Child 2" in child_names


class TestAgentConfigCRUD:
    """Test Agent Config CRUD operations"""

    def test_create_agent_config(self, db: Session, test_user: User) -> None:
        """Test creating an agent config"""
        config_data = {
            "name": "Test Config",
            "agent_type": "openai",
            "config": {"model": "gpt-4", "temperature": 0.7},
        }

        config = crud.create_agent_config(db, config_data, test_user.id)

        assert config is not None
        assert config.id is not None
        assert config.name == "Test Config"
        assert config.agent_type == "openai"
        assert config.owner_id == test_user.id

    def test_get_agent_config(self, db: Session, test_agent_config: AgentConfig) -> None:
        """Test getting an agent config by ID"""
        retrieved_config = crud.get_agent_config(db, test_agent_config.id)

        assert retrieved_config is not None
        assert retrieved_config.id == test_agent_config.id
        assert retrieved_config.name == test_agent_config.name

    def test_list_agent_configs(self, db: Session, test_user: User, test_agent_config: AgentConfig) -> None:
        """Test listing agent configs"""
        # Create another config
        config_data = {
            "name": "Another Config",
            "agent_type": "openai",
            "config": {"model": "gpt-3.5-turbo"},
        }
        crud.create_agent_config(db, config_data, test_user.id)

        # List all configs
        configs, count = crud.list_agent_configs(db, test_user.id)

        assert len(configs) >= 2
        assert count >= 2
        assert all(config.owner_id == test_user.id for config in configs)

    def test_list_agent_configs_with_type_filter(self, db: Session, test_user: User) -> None:
        """Test listing agent configs filtered by type"""
        # Create configs of different types
        crud.create_agent_config(
            db,
            {"name": "OpenAI Config", "agent_type": "openai", "config": {}},
            test_user.id
        )
        crud.create_agent_config(
            db,
            {"name": "Anthropic Config", "agent_type": "anthropic", "config": {}},
            test_user.id
        )

        # Filter by agent_type
        openai_configs, openai_count = crud.list_agent_configs(db, test_user.id, agent_type="openai")

        assert all(c.agent_type == "openai" for c in openai_configs)


class TestExecutionLogCRUD:
    """Test Execution Log CRUD operations"""

    def test_create_execution_log(self, db: Session, test_pdca_cycle: PDCACycle) -> None:
        """Test creating an execution log"""
        log = crud.create_execution_log(
            db,
            cycle_id=test_pdca_cycle.id,
            phase="plan",
            level="info",
            message="Test log message",
            metadata={"key": "value"},
        )

        assert log is not None
        assert log.id is not None
        assert log.cycle_id == test_pdca_cycle.id
        assert log.phase == "plan"
        assert log.level == "info"
        assert log.message == "Test log message"
        assert log.metadata == {"key": "value"}

    def test_get_cycle_logs(self, db: Session, test_pdca_cycle: PDCACycle) -> None:
        """Test getting logs for a cycle"""
        # Create multiple logs
        crud.create_execution_log(db, test_pdca_cycle.id, "plan", "info", "Log 1")
        crud.create_execution_log(db, test_pdca_cycle.id, "do", "warning", "Log 2")
        crud.create_execution_log(db, test_pdca_cycle.id, "check", "error", "Log 3")

        # Get logs
        logs = crud.get_cycle_logs(db, test_pdca_cycle.id)

        assert len(logs) >= 3
        assert all(log.cycle_id == test_pdca_cycle.id for log in logs)

        # Check ordering (most recent first)
        log_messages = [log.message for log in logs]
        assert "Log 1" in log_messages
        assert "Log 2" in log_messages
        assert "Log 3" in log_messages
