from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()


class HotkeyRequest(BaseModel):
    name: str


@router.post("/v1/vts/hotkey")
async def trigger_hotkey(payload: HotkeyRequest, request: Request) -> dict:
    controller = request.app.state.vts_controller
    await controller.trigger_hotkey(payload.name)
    return {"ok": True, "hotkey": payload.name}


@router.get("/v1/vts/status")
async def vts_status(request: Request) -> dict:
    controller = request.app.state.vts_controller
    return controller.status()
