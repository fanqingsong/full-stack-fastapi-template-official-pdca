"""WebSocket manager tests for web tests module."""

import uuid

import pytest


@pytest.mark.asyncio
async def test_websocket_manager_connect():
    """Test WebSocket connection management"""
    from app.web_tests.websocket import WebSocketManager

    manager = WebSocketManager()
    test_id = uuid.uuid4()

    # Mock websocket
    class MockWebSocket:
        async def accept(self):
            self.accepted = True

    ws = MockWebSocket()
    await manager.connect(test_id, ws)

    assert test_id in manager.active_connections
    assert manager.active_connections[test_id] == ws


@pytest.mark.asyncio
async def test_websocket_manager_disconnect():
    """Test WebSocket disconnection"""
    from app.web_tests.websocket import WebSocketManager

    manager = WebSocketManager()
    test_id = uuid.uuid4()

    class MockWebSocket:
        async def accept(self):
            self.accepted = True

    ws = MockWebSocket()
    await manager.connect(test_id, ws)
    manager.disconnect(test_id)

    assert test_id not in manager.active_connections


@pytest.mark.asyncio
async def test_websocket_manager_send_log():
    """Test sending log messages"""
    from app.web_tests.websocket import WebSocketManager

    manager = WebSocketManager()
    test_id = uuid.uuid4()

    class MockWebSocket:
        def __init__(self):
            self.messages = []

        async def accept(self):
            self.accepted = True

        async def send_json(self, data):
            self.messages.append(data)

    ws = MockWebSocket()
    await manager.connect(test_id, ws)

    await manager.send_log(test_id, "Test log message")

    assert len(ws.messages) == 1
    assert ws.messages[0] == {"type": "log", "data": "Test log message"}
