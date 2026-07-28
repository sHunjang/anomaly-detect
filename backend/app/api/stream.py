"""
프론트엔드가 연결할 WebSocket 엔드포인트
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.streaming.manager import manager

router = APIRouter()


@router.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            # 클라이언트가 뭔가 보낼 일은 없지만, 연결이 끊겼는지 감지하려면
            # 계속 뭔가를 "받으려고 대기"하는 상태가 필요함
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)