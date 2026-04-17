"""
WebSocket connection manager.
Pushes real-time burnout score updates to connected dashboard clients.
"""

from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections per user."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection for a user."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                conn for conn in self.active_connections[user_id]
                if conn != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_score_update(self, user_id: str, data: dict):
        """Push a score update to all connections for a user."""
        if user_id not in self.active_connections:
            return

        message = json.dumps(data)
        dead_connections = []

        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn, user_id)

    async def broadcast(self, data: dict):
        """Broadcast to all connected users."""
        message = json.dumps(data)
        for user_id in list(self.active_connections.keys()):
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    self.disconnect(connection, user_id)

    @property
    def connection_count(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())


# Singleton instance
manager = ConnectionManager()
