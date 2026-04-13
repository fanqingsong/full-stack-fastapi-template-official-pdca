"""WebSocket connection manager for web test execution."""

import asyncio
import logging
import uuid
from fastapi import WebSocket
from typing import Dict

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for web test execution"""

    def __init__(self):
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, test_id: uuid.UUID, websocket: WebSocket) -> None:
        """Accept and store a WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            self.active_connections[test_id] = websocket
        logger.info(f"WebSocket connected for test {test_id}")

    def disconnect(self, test_id: uuid.UUID) -> None:
        """Remove a WebSocket connection"""
        if test_id in self.active_connections:
            self.active_connections.pop(test_id)
            logger.info(f"WebSocket disconnected for test {test_id}")

    async def _send_message(self, test_id: uuid.UUID, message_type: str, data: any) -> bool:
        """
        Helper method to send messages to a WebSocket connection.

        Args:
            test_id: The test UUID
            message_type: Type of message (log, status, screenshot, complete, error)
            data: The data to send

        Returns:
            bool: True if message sent successfully, False otherwise
        """
        async with self._lock:
            websocket = self.active_connections.get(test_id)

        if not websocket:
            logger.warning(f"No WebSocket connection found for test {test_id}")
            return False

        try:
            await websocket.send_json({"type": message_type, "data": data})
            logger.debug(f"Sent {message_type} message to test {test_id}")
            return True
        except (WebSocketDisconnect, ConnectionResetError) as e:
            logger.warning(f"WebSocket disconnected for test {test_id}: {e}")
            self.disconnect(test_id)
            return False
        except RuntimeError as e:
            logger.error(f"Runtime error sending to test {test_id}: {e}")
            self.disconnect(test_id)
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending to test {test_id}: {e}")
            self.disconnect(test_id)
            return False

    async def send_log(self, test_id: uuid.UUID, log: str) -> None:
        """Send a log message to the connected client"""
        await self._send_message(test_id, "log", log)

    async def send_status(self, test_id: uuid.UUID, status: str) -> None:
        """Send a status update to the connected client"""
        await self._send_message(test_id, "status", status)

    async def send_screenshot(self, test_id: uuid.UUID, screenshot_url: str) -> None:
        """Send a screenshot URL to the connected client"""
        await self._send_message(test_id, "screenshot", screenshot_url)

    async def send_complete(self, test_id: uuid.UUID, result: dict) -> None:
        """Send completion message to the connected client"""
        await self._send_message(test_id, "complete", result)

    async def send_error(self, test_id: uuid.UUID, error: str) -> None:
        """Send an error message to the connected client"""
        await self._send_message(test_id, "error", error)
