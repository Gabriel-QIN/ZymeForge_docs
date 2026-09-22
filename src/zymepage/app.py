"""FastAPI application for the ZymePage model catalog."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from zymeforge.function.adapters import ModelBackendUnavailable

from zymepage.catalog import get_tool, list_tools

PACKAGE_DIR = Path(__file__).parent


def create_app() -> FastAPI:
    """Build the web application without mutating the scientific registry."""
    application = FastAPI(
        title="ZymeForge Tools",
        description="Registry-backed enzyme discovery and engineering model catalog.",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    application.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
    templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
    docs_url = os.getenv(
        "ZYMEFORGE_DOCS_URL", "https://gabriel-qin.github.io/ZymeForge_docs/"
    )

    @application.get("/", include_in_schema=False)
    async def home() -> RedirectResponse:
        return RedirectResponse("/tools")

    @application.get("/tools", response_class=HTMLResponse, include_in_schema=False)
    async def tools_page(request: Request) -> HTMLResponse:
        tools = list_tools()
        categories = sorted({tool["category"] for tool in tools})
        return templates.TemplateResponse(
            request=request,
            name="catalog.html",
            context={
                "tools": tools,
                "categories": categories,
                "docs_url": docs_url,
                "page": "tools",
            },
        )

    @application.get(
        "/tools/{identifier}", response_class=HTMLResponse, include_in_schema=False
    )
    async def tool_page(request: Request, identifier: str) -> HTMLResponse:
        resolved = get_tool(identifier)
        if resolved is None:
            raise HTTPException(status_code=404, detail="Unknown registered tool")
        _, tool = resolved
        return templates.TemplateResponse(
            request=request,
            name="tool.html",
            context={"tool": tool, "docs_url": docs_url, "page": "tools"},
        )

    @application.get("/api/models")
    async def models_api() -> dict[str, Any]:
        tools = list_tools()
        return {"count": len(tools), "models": tools}

    @application.get("/api/models/{identifier}")
    async def model_api(identifier: str) -> dict[str, Any]:
        resolved = get_tool(identifier)
        if resolved is None:
            raise HTTPException(status_code=404, detail="Unknown registered tool")
        return resolved[1]

    @application.post("/api/models/{identifier}/predict")
    async def predict(identifier: str, payload: dict[str, Any]) -> dict[str, Any]:
        resolved = get_tool(identifier)
        if resolved is None:
            raise HTTPException(status_code=404, detail="Unknown registered tool")
        model_class, tool = resolved
        missing = [field for field in tool["inputs"] if not payload.get(field)]
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing inputs: {', '.join(missing)}")
        try:
            predictions = model_class(device="cuda").predict(payload)
        except ModelBackendUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"{tool['name']} is registered, but its upstream weights and runner "
                    "have not been configured on this deployment."
                ),
            ) from exc
        return {
            "model": tool,
            "predictions": [prediction.model_dump(mode="json") for prediction in predictions],
        }

    return application


app = create_app()
