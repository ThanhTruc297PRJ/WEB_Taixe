import asyncio
import time
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # room_id -> danh sách WebSocket
        self.rooms: dict[str, list[WebSocket]] = defaultdict(list)

        # WebSocket -> thời điểm heartbeat gần nhất
        self.last_heartbeat: dict[WebSocket, float] = {}

        # Kiểm tra mỗi 10 giây
        self.heartbeat_interval = 10

        # Quá 30 giây không heartbeat -> xem như mất kết nối
        self.heartbeat_timeout = 30

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()

        self.rooms[room_id].append(websocket)
        self.last_heartbeat[websocket] = time.time()

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.rooms and websocket in self.rooms[room_id]:
            self.rooms[room_id].remove(websocket)

        self.last_heartbeat.pop(websocket, None)

        if room_id in self.rooms and not self.rooms[room_id]:
            del self.rooms[room_id]

    def update_heartbeat(self, websocket: WebSocket):
        self.last_heartbeat[websocket] = time.time()

    async def send_personal_message(
        self,
        message: dict,
        websocket: WebSocket,
    ):
        await websocket.send_json(message)

    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
    ):
        if room_id not in self.rooms:
            return

        disconnected = []

        for connection in list(self.rooms[room_id]):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection, room_id)

    def get_room_size(self, room_id: str) -> int:
        return len(self.rooms.get(room_id, []))

    async def heartbeat_monitor(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval)

            current_time = time.time()

            for room_id, connections in list(self.rooms.items()):
                for websocket in list(connections):

                    last_seen = self.last_heartbeat.get(
                        websocket,
                        current_time,
                    )

                    if current_time - last_seen > self.heartbeat_timeout:
                        try:
                            await websocket.close(
                                code=1001,
                                reason="Heartbeat timeout",
                            )
                        except Exception:
                            pass

                        self.disconnect(websocket, room_id)


manager = ConnectionManager()