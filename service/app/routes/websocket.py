from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import manager

router = APIRouter()


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)

    await manager.broadcast_to_room(
        room_id,
        {
            "type": "system",
            "message": "Client connected",
            "room": room_id,
            "connections": manager.get_room_size(room_id),
        },
    )

    try:
        while True:
            data = await websocket.receive_json()

            # Có dữ liệu từ client => connection vẫn còn sống
            manager.update_heartbeat(websocket)

            # SUB-03: Heartbeat Ping-Pong
            if data.get("type") == "ping":
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "room": room_id,
                    },
                    websocket,
                )
                continue

            # SUB-04: Realtime Alert Android -> Web Admin
            if data.get("type") == "alert":
                alert = {
                    "type": "alert",
                    "room": room_id,
                    "driver_id": data.get("driver_id"),
                    "alert_type": data.get("alert_type"),
                    "severity": data.get("severity", "medium"),
                    "message": data.get("message"),
                }

                await manager.broadcast_to_room(room_id, alert)
                continue

            # Dữ liệu bình thường -> broadcast cho các client cùng room
            await manager.broadcast_to_room(
                room_id,
                {
                    "type": "message",
                    "room": room_id,
                    "data": data,
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

        await manager.broadcast_to_room(
            room_id,
            {
                "type": "system",
                "message": "Client disconnected",
                "room": room_id,
                "connections": manager.get_room_size(room_id),
            },
        )
