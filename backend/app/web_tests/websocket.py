"""WebSocket connection manager for web test execution."""

import uuid
from fastapi import WebSocket
from typing import Dict


class WebSocketManager:
    """Manages WebSocket connections for web test execution"""

    def __init__(self):
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}

    async def connect(self, test_id: uuid.UUID, websocket: WebSocket) -> None:
        """Accept and store a WebSocket connection"""
        await websocket.accept()
        self.active_connections[test_id] = websocket

    def disconnect(self, test_id: uuid.UUID) -> None:
        """Remove a WebSocket connection"""
        self.active_connections.pop(test_id, None)

    async def send_log(self, test_id: uuid.UUID, log: str) -> None:
        """Send a log message to the connected client"""
        if websocket := self.active_connections.get(test_id):
            try:
                await websocket.send_json({"type": "log", "data": log})
            except Exception:
                # Connection may be closed, remove it
                self.disconnect(test_id)

    async def send_status(self, test_id: uuid.UUID, status: str) -> None:
        """Send a status update to the connected client"""
        if websocket := self.active_connections.get(test_id):
            try:
                await websocket.send_json({"type": "status", "data": status})
            except Exception:
                self.disconnect(test_id)

    async def send_screenshot(self, test_id: uuid.UUID, screenshot_url: str) -> None:
        """Send a screenshot URL to the connected client"""
        if websocket := self.active_connections.get(test_id):
            try:
                await websocket.send_json({"type": "screenshot", "data": screenshot_url})
            except Exception:
                self.disconnect(test_id)

    async def send_complete(self, test_id: uuid.UUID, result: dict) -> None:
        """Send completion message to the connected client"""
        if websocket := self.active_connections.get(test_id):
            try:
                await websocket.send_json({"type": "complete", "data": result})
            except Exception:
                self.disconnect(test_id)

    async def send_error(self, test_id: uuid.UUID, error: str) -> None:
        """Send an error message to the connected client"""
        if websocket := self.active_connections.get(test_id):
            try:
                await websocket.send_json({"type": "error", "data": error})
            except Exception:
                self.disconnect(test_id)
