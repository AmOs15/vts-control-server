#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import pyvts


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"").strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_env(name: str, default: Optional[str] = None, *, cast: Optional[Callable[[str], Any]] = None) -> Any:
    value = os.getenv(name, default)
    if value is None or value == "":
        return value
    if cast is None:
        return value
    try:
        return cast(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid {name}: {value}") from exc


def create_vts(
    *,
    plugin_name: str,
    plugin_developer: str,
    token_path: str,
    host: str,
    port: int,
) -> Any:
    vts_factory = getattr(pyvts, "vts", None) or getattr(pyvts, "VTS", None)
    if vts_factory is None:
        raise SystemExit("pyvts API not found (missing vts/VTS)")

    token_path_str = str(token_path)
    candidates = [
        dict(
            plugin_name=plugin_name,
            plugin_developer=plugin_developer,
            token_path=token_path_str,
            host=host,
            port=port,
        ),
        dict(
            plugin_name=plugin_name,
            plugin_developer=plugin_developer,
            token_path=token_path_str,
        ),
    ]

    for kwargs in candidates:
        try:
            return vts_factory(**kwargs)
        except TypeError:
            continue

    positional = [
        (plugin_name, plugin_developer, token_path_str, host, port),
        (plugin_name, plugin_developer, token_path_str),
    ]
    for args in positional:
        try:
            return vts_factory(*args)
        except TypeError:
            continue

    raise SystemExit("Unsupported pyvts constructor signature")


def get_request_builder(module: Any, *names: str) -> Optional[Callable[..., Any]]:
    for name in names:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    return None


def resolve_hotkey_id(response: Any, hotkey_name: str) -> Optional[str]:
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


async def send_request(vts: Any, request: Any) -> Any:
    if hasattr(vts, "request"):
        return await vts.request(request)
    if hasattr(vts, "send"):
        return await vts.send(request)
    raise SystemExit("pyvts client has no request/send method")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger a VTS hotkey via pyvts")
    parser.add_argument("--hotkey", required=True, help="Hotkey name (e.g. wave)")
    parser.add_argument("--host", help="Override VTS_HOST")
    parser.add_argument("--port", type=int, help="Override VTS_PORT")
    parser.add_argument("--plugin-name", help="Override VTS_PLUGIN_NAME")
    parser.add_argument("--plugin-developer", help="Override VTS_PLUGIN_DEVELOPER")
    parser.add_argument("--token-path", help="Override VTS_TOKEN_PATH")
    args = parser.parse_args()

    load_dotenv(Path(".env"))

    host = args.host or get_env("VTS_HOST", "localhost")
    port = args.port or get_env("VTS_PORT", "8001", cast=int)
    plugin_name = args.plugin_name or get_env("VTS_PLUGIN_NAME", "vts-control-server")
    plugin_developer = args.plugin_developer or get_env("VTS_PLUGIN_DEVELOPER", "vts-control-server")
    token_path = args.token_path or get_env("VTS_TOKEN_PATH", ".secrets/vts_token.json")

    token_path_obj = Path(token_path)
    token_path_obj.parent.mkdir(parents=True, exist_ok=True)

    vts = create_vts(
        plugin_name=plugin_name,
        plugin_developer=plugin_developer,
        token_path=str(token_path_obj),
        host=str(host),
        port=int(port),
    )

    print(f"Connecting to VTS ws://{host}:{port} ...")
    await vts.connect()

    try:
        if not token_path_obj.exists():
            print("Requesting auth token (first run)...")
            await vts.request_authenticate_token()
        else:
            print("Token file exists; skipping token request.")

        print("Authenticating...")
        auth_response = await vts.request_authenticate()
        if not is_authenticated(auth_response):
            print("Authentication failed; requesting new token...")
            await vts.request_authenticate_token()
            auth_response = await vts.request_authenticate()
            if not is_authenticated(auth_response):
                raise SystemExit("Authentication failed after token refresh")

        vts_request = getattr(pyvts, "vts_request", None)
        if vts_request is None:
            raise SystemExit("pyvts.vts_request not found; update pyvts")

        list_fn = get_request_builder(vts_request, "requestHotKeyList", "requestHotkeyList")
        trigger_fn = get_request_builder(vts_request, "requestTriggerHotKey", "requestTriggerHotkey")
        if trigger_fn is None:
            raise SystemExit("pyvts hotkey trigger request not found")

        hotkey_id = args.hotkey
        if list_fn is not None:
            response = await send_request(vts, list_fn())
            resolved = resolve_hotkey_id(response, args.hotkey)
            if resolved:
                hotkey_id = resolved

        print(f"Triggering hotkey: {hotkey_id}")
        await send_request(vts, trigger_fn(hotkey_id))

        print("Done.")
        return 0
    finally:
        if hasattr(vts, "close"):
            await vts.close()


def is_authenticated(response: Any) -> bool:
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict) and "authenticated" in data:
            return bool(data.get("authenticated"))
    return True


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
