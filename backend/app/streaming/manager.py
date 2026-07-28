"""
WebSocket에 연결된 클라이언트(브라우저)들을 관리하는 매니저
- 여러 사람이 동시에 대시보드를 열어도, 모두에게 똑같은 실시간 데이터를 뿌려줘야 하므로
    "지금 연결된 사람 목록"을 들고 있다가 새 데이터가 생기면 전원에게 전송
"""

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()    # 클라이언트의 연결 요청 수락

        self.active_connections.append(websocket)
        print(f"클라이언트 연결됨. 현재 {len(self.active_connections)}명 접속 중")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"클라이언트 연결 종료. 현재 {len(self.active_connections)}명 접속 중")

    async def broadcast(self, message: dict):
        """연결된 모든 클라이언트에게 같은 메세지 전송"""
        # 전송 중 연결이 끊긴 클라이언트가 있을 수 있어서, 끊긴 걸 따로 모아뒀다가 나중에 정리
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:  # noqa: BLE001
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()