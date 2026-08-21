from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.exc import SQLAlchemyError
from database.connection import async_session
from database.models import Group, GroupMessage, GroupUser
from handlers.social_auth import verify_access_token
from sqlalchemy import select

router = APIRouter(prefix='/ws', tags=['WebSocket'])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, group_id: int):
        await ws.accept()
        if group_id not in self.active_connections:
            self.active_connections[group_id] = []
        self.active_connections[group_id].append(ws)

    async def disconnect(self, group_id: int, ws: WebSocket):
        connections = self.active_connections.get(group_id)
        if connections and ws in connections:
            connections.remove(ws)
            if not connections:
                self.active_connections.pop(group_id, None)

    async def broadcast(self, group_id: int, data: dict):
        connections = self.active_connections.get(group_id, [])
        disconnected = []

        for ws in connections.copy():
            try:
                await ws.send_json(data)
            except WebSocketDisconnect:
                disconnected.append(ws)

        for ws in disconnected:
            await self.disconnect(group_id, ws)

manager = ConnectionManager()


@router.websocket('/group/{group_id}/')
async def chat(ws: WebSocket, group_id: int, access_token: str):
    try:
        current_user = await verify_access_token(access_token)
    except HTTPException as e:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e.detail))
        return

    async with async_session() as db:
        result = await db.execute(select(Group).where(Group.id == group_id))
        if not result.scalar_one_or_none():
            await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason='Group not found')
            return

        group_user_res = await db.execute(
            select(GroupUser).where(GroupUser.group == group_id, GroupUser.user == current_user['id'])
        )
        if not group_user_res.scalar_one_or_none():
            await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason='You are not a member of this group')
            return

    await manager.connect(ws, group_id)
    await ws.send_json({
        'type': 'connection.established',
        'data': {
            'group_id': group_id,
            'user_id': current_user['id'],
            'message': 'Connection established'
        }
    })

    try:
        while True:
            payload = await ws.receive_json()

            if isinstance(payload, dict):
                msg_text = payload.get('message', '').strip()
            else:
                msg_text = str(payload).strip()

            if not msg_text:
                await ws.send_json({'type': 'error', 'detail': 'Message cannot be empty'})
                continue

            if len(msg_text) > 5000:
                await ws.send_json({'type': 'error', 'detail': 'Message length cannot be longer than 5000 characters'})
                continue

            async with async_session() as db:
                try:
                    new_message = GroupMessage(
                        group=group_id,
                        user=current_user['id'],
                        message=msg_text
                    )

                    db.add(new_message)
                    await db.commit()
                    await db.refresh(new_message)

                    data = {
                        'type': 'message',
                        'data': {
                            'id': new_message.id,
                            'group_id': group_id,
                            'user_id': current_user['id'],
                            'message': msg_text
                        }
                    }

                    await manager.broadcast(group_id, data)

                except SQLAlchemyError:
                    await db.rollback()
                    await ws.send_json({
                        'type': 'error',
                        'detail': 'Failed to save message to database'
                    })
                    continue

    except WebSocketDisconnect:
        await manager.disconnect(group_id, ws)