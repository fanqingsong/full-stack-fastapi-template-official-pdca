"""Web automation testing database models."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models import User


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class WebTestBase(SQLModel):
    url: str = Field(max_length=2048)
    description: str = Field(max_length=5000)
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = Field(
        default="pending"
    )


class WebTest(WebTestBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")

    owner: "User" = Relationship(back_populates="web_tests")
    results: list["WebTestResult"] = Relationship(back_populates="test")


class WebTestPublic(WebTestBase):
    id: uuid.UUID
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    owner_id: uuid.UUID
    has_result: bool = False


class WebTestsPublic(SQLModel):
    data: list[WebTestPublic]
    count: int


class WebTestCreate(SQLModel):
    url: str = Field(max_length=2048)
    description: str = Field(min_length=10, max_length=5000)


class WebTestResultBase(SQLModel):
    success: bool
    execution_logs: str


class WebTestResult(WebTestResultBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    test_id: uuid.UUID = Field(
        foreign_key="webtest.id", nullable=False, ondelete="CASCADE"
    )

    error_message: str | None = None
    screenshot_path: str | None = None
    video_path: str | None = None
    execution_duration: float | None = None
    claude_version: str | None = None
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    test: WebTest = Relationship(back_populates="results")


class WebTestResultPublic(WebTestResultBase):
    id: uuid.UUID
    test_id: uuid.UUID
    error_message: str | None = None
    screenshot_url: str | None = None
    video_url: str | None = None
    execution_duration: float | None = None
    created_at: datetime | None = None
