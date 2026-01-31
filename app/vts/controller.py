from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Optional

import pyvts
from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


_RETRY = retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


class VTSController:
    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 8001,
        plugin_name: str = "vts-control-server",
        plugin_developer: str = "vts-control-server",
        token_path: str = ".secrets/vts_token.json",
    ) -> None:
        self.host = host
        self.port = port
        self.plugin_name = plugin_name
        self.plugin_developer = plugin_developer
        self.token_path = Path(token_path)
        self._vts: Any = None
        self._connected = False
        self._authenticated = False
        self._lock = asyncio.Lock()

    @_RETRY
    async def connect(self) -> None:
        if self._vts is None:
            self._vts = self._create_client()
        try:
            await self._vts.connect()
            self._connected = True
        except Exception:
            await self._reset_connection()
            raise

    @_RETRY
    async def ensure_authenticated(self) -> None:
        await self._ensure_authenticated()

    async def trigger_hotkey(self, hotkey_id_or_name: str) -> None:
        async with self._lock:
            await self.ensure_authenticated()
            await self._trigger_hotkey_with_retry(hotkey_id_or_name)

    def _create_client(self) -> Any:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path_str = str(self.token_path)

        vts_factory = getattr(pyvts, "vts", None) or getattr(pyvts, "VTS", None)
        if vts_factory is None:
            raise RuntimeError("pyvts API not found (missing vts/VTS)")

        candidates = [
            dict(
                plugin_name=self.plugin_name,
                plugin_developer=self.plugin_developer,
                token_path=token_path_str,
                host=self.host,
                port=self.port,
            ),
            dict(
                plugin_name=self.plugin_name,
                plugin_developer=self.plugin_developer,
                token_path=token_path_str,
            ),
        ]
        for kwargs in candidates:
            try:
                return vts_factory(**kwargs)
            except TypeError:
                continue

        positional = [
            (self.plugin_name, self.plugin_developer, token_path_str, self.host, self.port),
            (self.plugin_name, self.plugin_developer, token_path_str),
        ]
        for args in positional:
            try:
                return vts_factory(*args)
            except TypeError:
                continue

        raise RuntimeError("Unsupported pyvts constructor signature")

    async def _ensure_authenticated(self) -> None:
        if not self._connected:
            await self.connect()

        if self._authenticated:
            return

        request_token = getattr(self._vts, "request_authenticate_token", None)
        request_auth = getattr(self._vts, "request_authenticate", None)
        if not callable(request_token) or not callable(request_auth):
            raise RuntimeError("pyvts authentication methods not found")

        if not self.token_path.exists():
            await request_token()

        auth_response = await request_auth()
        if not _is_authenticated(auth_response):
            await request_token()
            auth_response = await request_auth()
            if not _is_authenticated(auth_response):
                raise RuntimeError("Authentication failed after token refresh")

        self._authenticated = True

    @_RETRY
    async def _trigger_hotkey_with_retry(self, hotkey_id_or_name: str) -> None:
        try:
            await self._trigger_hotkey_once(hotkey_id_or_name)
        except Exception:
            await self._reset_connection()
            raise

    async def _trigger_hotkey_once(self, hotkey_id_or_name: str) -> None:
        vts_request = getattr(pyvts, "vts_request", None)
        if vts_request is None:
            raise RuntimeError("pyvts.vts_request not found")

        list_fn = _get_request_builder(vts_request, "requestHotKeyList", "requestHotkeyList")
        trigger_fn = _get_request_builder(vts_request, "requestTriggerHotKey", "requestTriggerHotkey")
        if trigger_fn is None:
            raise RuntimeError("pyvts hotkey trigger request not found")

        hotkey_id = hotkey_id_or_name
        if list_fn is not None:
            response = await _send_request(self._vts, list_fn())
            resolved = _resolve_hotkey_id(response, hotkey_id_or_name)
            if resolved:
                hotkey_id = resolved

        await _send_request(self._vts, trigger_fn(hotkey_id))

    async def _reset_connection(self) -> None:
        self._connected = False
        self._authenticated = False
        if self._vts is None:
            return
        if hasattr(self._vts, "close"):
            try:
                await self._vts.close()
            except Exception:
                logger.warning("Failed to close VTS connection", exc_info=True)
        self._vts = None


def _get_request_builder(module: Any, *names: str) -> Optional[Callable[..., Any]]:
    for name in names:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    return None


def _resolve_hotkey_id(response: Any, hotkey_name: str) -> Optional[str]:
    if not isinstance(response, dict):
        return None
    data = response.get("data")
    if not isinstance(data, dict):
        return None
    items = data.get("availableHotkeys") or data.get("hotkeys")
    if not isinstance(items, list):
        return None
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("hotkeyName")
        if not name:
            continue
        if name.lower() != hotkey_name.lower():
            continue
        return item.get("hotkeyID") or item.get("id") or name
    return None


async def _send_request(vts: Any, request: Any) -> Any:
    if hasattr(vts, "request"):
        return await vts.request(request)
    if hasattr(vts, "send"):
        return await vts.send(request)
    raise RuntimeError("pyvts client has no request/send method")


def _is_authenticated(response: Any) -> bool:
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict) and "authenticated" in data:
            return bool(data.get("authenticated"))
    return True
