from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, User
from app.pdca.models import PDCACycle, AgentConfig, ExecutionLog
from tests.utils.user import authentication_token_from_email, create_random_user
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(ExecutionLog)
        session.execute(statement)
        statement = delete(PDCACycle)
        session.execute(statement)
        statement = delete(AgentConfig)
        session.execute(statement)
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user for PDCA tests"""
    return create_random_user(db)


@pytest.fixture
def test_pdca_cycle(db: Session, test_user: User) -> PDCACycle:
    """创建测试用的PDCA循环"""
    cycle = PDCACycle(
        name="Test PDCA Cycle",
        agent_type="openai",
        state_data={
            "goal": "Test goal",
            "agent_input": {"prompt": "test"},
            "plan_details": {},
            "check_criteria": {}
        },
        owner_id=test_user.id
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


@pytest.fixture
def test_agent_config(db: Session, test_user: User) -> AgentConfig:
    """创建测试用的Agent配置"""
    config = AgentConfig(
        name="Test OpenAI Config",
        agent_type="openai",
        config={"model": "gpt-4", "temperature": 0.7},
        owner_id=test_user.id
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config
