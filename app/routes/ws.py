from __future__ import annotations

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.vts.mapping import resolve_hotkey


router = APIRouter()


@router.websocket("/v1/ws")
async def ws_actions(websocket: WebSocket) -> None:
    await websocket.accept()
    print("[ws] connected")
    try:
        while True:
            payload = await websocket.receive_json()
            action = _extract_action(payload)
            if action is None:
                msg = {"ok": False, "error": "invalid payload"}
                print("[ws] invalid payload:", payload)
                await websocket.send_json(msg)
                continue

            action_id = action.get("actionId") or action.get("action_id")
            if not action_id:
                msg = {"ok": False, "error": "missing actionId"}
                print("[ws] missing actionId:", payload)
                await websocket.send_json(msg)
                continue

            hotkey = resolve_hotkey(action_id)
            if hotkey is None:
                msg = {"ok": False, "error": f"unknown actionId: {action_id}"}
                print("[ws] unknown actionId:", action_id)
                await websocket.send_json(msg)
                continue

            controller = websocket.app.state.vts_controller
            try:
                await controller.trigger_hotkey(hotkey)
                msg = {"ok": True, "actionId": action_id, "hotkey": hotkey}
                print("[ws] triggered:", msg)
                await websocket.send_json(msg)
            except Exception as exc:
                msg = {"ok": False, "error": str(exc), "actionId": action_id, "hotkey": hotkey}
                print("[ws] trigger failed:", msg)
                await websocket.send_json(msg)
    except WebSocketDisconnect:
        print("[ws] disconnected")


def _extract_action(payload: Any) -> dict | None:
    if isinstance(payload, dict) and ("actionId" in payload or "action_id" in payload):
        return payload
    if isinstance(payload, dict):
        action = payload.get("action")
        if isinstance(action, dict):
            return action
    return None
