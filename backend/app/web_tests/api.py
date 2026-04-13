"""API routes for web automation testing."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.models import Message
from app.web_tests import crud
from app.web_tests.executor import check_claude_available, validate_url
from app.web_tests.models import (
    WebTest,
    WebTestCreate,
    WebTestPublic,
    WebTestsPublic,
    WebTestResultPublic,
)
from app.web_tests.websocket import WebSocketManager

router = APIRouter(prefix="/web-tests", tags=["web-tests"])
websocket_manager = WebSocketManager()


@router.post("/", response_model=WebTestPublic, status_code=status.HTTP_201_CREATED)
def create_web_test(
    *, session: SessionDep, current_user: CurrentUser, web_test_in: WebTestCreate
) -> Any:
    """
    Create a new web test.

    Validates the URL format and checks Claude CLI availability.
    Also enforces concurrency limits.
    """
    # Validate URL format using executor
    if not validate_url(web_test_in.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format. Must start with http:// or https://"
        )

    # Check Claude CLI availability
    if not check_claude_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claude CLI not available. Please ensure it is installed and accessible."
        )

    # Check concurrency limit
    running_count = crud.count_web_tests_by_status(
        session=session, owner_id=current_user.id, status="running"
    )
    if running_count >= settings.MAX_CONCURRENT_TESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum concurrent tests limit ({settings.MAX_CONCURRENT_TESTS}) reached. Please wait for current tests to complete."
        )

    # Create the web test
    web_test = crud.create_web_test(
        session=session,
        web_test_create=web_test_in,
        owner_id=current_user.id
    )

    # TODO: Schedule background task to execute the test (Task #19)

    return web_test


@router.get("/", response_model=WebTestsPublic)
def read_web_tests(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status_filter: str | None = Query(None, alias="status"),
) -> Any:
    """
    Retrieve web tests.

    Supports pagination and status filtering.
    Only returns tests owned by the current user.
    """
    if status_filter:
        # Validate status filter
        valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Must be one of {valid_statuses}"
            )

        count = crud.count_web_tests_by_status(
            session=session, owner_id=current_user.id, status=status_filter
        )

        # Get filtered tests
        statement = (
            select(WebTest)
            .where(WebTest.owner_id == current_user.id, WebTest.status == status_filter)
            .order_by(WebTest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        web_tests = session.exec(statement).all()
    else:
        # Get all tests
        count = crud.count_web_tests_by_owner(
            session=session, owner_id=current_user.id
        )
        web_tests = crud.get_web_tests_by_owner(
            session=session, owner_id=current_user.id, skip=skip, limit=limit
        )

    # Add has_result flag to each test
    web_tests_public = []
    for test in web_tests:
        test_dict = WebTestPublic.model_validate(test).model_dump()
        test_dict["has_result"] = len(test.results) > 0
        web_tests_public.append(WebTestPublic(**test_dict))

    return WebTestsPublic(data=web_tests_public, count=count)


@router.get("/{id}", response_model=WebTestPublic)
def read_web_test(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get a specific web test by ID.

    Only returns tests owned by the current user.
    """
    web_test = crud.get_web_test_by_id(session=session, web_test_id=id)

    if not web_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web test not found"
        )

    if not current_user.is_superuser and (web_test.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Add has_result flag
    test_dict = WebTestPublic.model_validate(web_test).model_dump()
    test_dict["has_result"] = len(web_test.results) > 0

    return WebTestPublic(**test_dict)


@router.delete("/{id}")
def delete_web_test(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a web test.

    Only allows deletion of tests owned by the current user.
    Only allows deletion of pending or failed tests (not running tests).
    """
    web_test = crud.get_web_test_by_id(session=session, web_test_id=id)

    if not web_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web test not found"
        )

    if not current_user.is_superuser and (web_test.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Only allow deletion of pending or failed tests
    if web_test.status == "running":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete running test. Cancel it first."
        )

    crud.delete_web_test(session=session, db_web_test=web_test)

    return Message(message="Web test deleted successfully")


@router.post("/{id}/retry", response_model=WebTestPublic)
def retry_web_test(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Retry a failed or cancelled web test.

    Resets the test status to "pending" and reschedules execution.
    Only allows retrying tests owned by the current user.
    """
    web_test = crud.get_web_test_by_id(session=session, web_test_id=id)

    if not web_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web test not found"
        )

    if not current_user.is_superuser and (web_test.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check Claude CLI availability
    if not check_claude_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claude CLI not available. Please ensure it is installed and accessible."
        )

    # Check concurrency limit
    running_count = crud.count_web_tests_by_status(
        session=session, owner_id=current_user.id, status="running"
    )
    if running_count >= settings.MAX_CONCURRENT_TESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum concurrent tests limit ({settings.MAX_CONCURRENT_TESTS}) reached. Please wait for current tests to complete."
        )

    # Reset status to pending
    updated_web_test = crud.update_web_test_status(
        session=session, db_web_test=web_test, status="pending"
    )

    # TODO: Reschedule background task to execute the test (Task #19)

    return updated_web_test


@router.get("/{id}/result", response_model=WebTestResultPublic)
def read_web_test_result(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get the result for a web test.

    Returns the most recent result for the test.
    Only returns results for tests owned by the current user.
    """
    web_test = crud.get_web_test_by_id(session=session, web_test_id=id)

    if not web_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web test not found"
        )

    if not current_user.is_superuser and (web_test.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    result = crud.get_web_test_result_by_test_id(session=session, test_id=id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    # Convert paths to URLs (placeholder - actual URL generation depends on MinIO setup)
    result_dict = WebTestResultPublic.model_validate(result).model_dump()
    # TODO: Generate proper URLs for screenshot and video using MinIO

    return WebTestResultPublic(**result_dict)


@router.websocket("/{id}")
async def websocket_web_test(
    websocket: WebSocket,
    id: uuid.UUID,
    token: str = Query(..., description="JWT authentication token")
) -> None:
    """
    WebSocket endpoint for real-time web test updates.

    Requires a valid JWT token via query parameter for authentication.
    """
    import jwt
    from app.core import security
    from app.core.db import engine
    from app.models import User, TokenPayload

    # Verify authentication token
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        # Get user from database
        from sqlmodel import Session
        with Session(engine) as session:
            user = session.get(User, token_data.sub)
            if not user or not user.is_active:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            # Get the web test
            web_test = crud.get_web_test_by_id(session=session, web_test_id=id)

            if not web_test:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            if not user.is_superuser and (web_test.owner_id != user.id):
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            # Accept the WebSocket connection
            await websocket_manager.connect(test_id=id, websocket=websocket)

            # Send current status
            await websocket_manager.send_status(id, web_test.status)

            # Keep connection alive and handle incoming messages
            try:
                while True:
                    # Receive and ignore any client messages
                    # (client is only listening for updates)
                    await websocket.receive_text()
            except WebSocketDisconnect:
                websocket_manager.disconnect(id)
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        websocket_manager.disconnect(id)
