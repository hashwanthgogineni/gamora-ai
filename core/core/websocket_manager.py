"""
WebSocket Manager - Real-time communication
"""

import logging
from typing import Dict, Set
from fastapi import WebSocket
import json

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections: {project_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        
        self.active_connections[project_id].add(websocket)
        logger.info(f"WebSocket connected for project: {project_id}")
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove WebSocket connection"""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        
        logger.info(f"WebSocket disconnected for project: {project_id}")
    
    async def send_message(self, project_id: str, message: dict):
        """Send message to all connections for a project"""
        if project_id not in self.active_connections:
            return
        
        # Send to all active connections
        dead_connections = set()
        for websocket in self.active_connections[project_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                dead_connections.add(websocket)
        
        # Clean up dead connections
        for websocket in dead_connections:
            self.disconnect(websocket, project_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        for project_id in list(self.active_connections.keys()):
            await self.send_message(project_id, message)
    
    def get_connection_count(self, project_id: str = None) -> int:
        """Get number of active connections"""
        if project_id:
            return len(self.active_connections.get(project_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())
