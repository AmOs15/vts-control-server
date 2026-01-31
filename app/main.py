from __future__ import annotations

from fastapi import FastAPI

from app.routes.vts_debug import router as vts_debug_router
from app.settings import Settings
from app.vts import VTSController


def create_app() -> FastAPI:
    settings = Settings()
    controller = VTSController(
        host=settings.host,
        port=settings.port,
        plugin_name=settings.plugin_name,
        plugin_developer=settings.plugin_developer,
        token_path=settings.token_path,
    )

    app = FastAPI(title="vts-control-server")
    app.state.vts_controller = controller
    app.include_router(vts_debug_router)
    return app


app = create_app()
