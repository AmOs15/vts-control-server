from __future__ import annotations

ACTION_TO_HOTKEY = {
    "wave": "HK_WAVE",
    "happy": "HK_HAPPY",
}


def resolve_hotkey(action_id: str) -> str | None:
    return ACTION_TO_HOTKEY.get(action_id)
