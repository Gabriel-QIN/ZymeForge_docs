"""FastAPI application for the ZymePage model catalog."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from zymeforge.bootstrap import build_reaction_workflow
from zymeforge.core.models import ReactionContext
from zymeforge.function.adapters import ModelBackendUnavailable

from zymepage.catalog import get_tool, list_models, list_registry_groups, list_tools

PACKAGE_DIR = Path(__file__).parent
REPOSITORY_DIR = PACKAGE_DIR.parents[1]


class ReactionMiningRequest(BaseModel):
    """Validated public request for the ZymeForge reaction mining workflow."""

    reaction: str = Field(min_length=3, description="Reaction SMILES: substrates>>products")
    top_k: int = Field(default=20, ge=1, le=1000)
    ph: float | None = Field(default=None, ge=0.0, le=14.0)
    temperature_c: float | None = None


@lru_cache(maxsize=4)
def _workflow(catalog_path: str):
    return build_reaction_workflow(catalog_path)


def create_app() -> FastAPI:
    """Build the web application without mutating the scientific registry."""
    application = FastAPI(
        title="ZymeForge Tools",
        description="Registry-backed enzyme discovery and engineering model catalog.",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    origins = [
        origin.strip()
        for origin in os.getenv(
            "ZYMEFORGE_CORS_ORIGINS",
            "https://gabriel-qin.github.io,http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
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
                "groups": list_registry_groups(),
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
        models = list_models()
        return {"count": len(models), "models": models}

    @application.get("/api/tools")
    async def tools_api() -> dict[str, Any]:
        tools = list_tools()
        return {"count": len(tools), "tools": tools}

    @application.get("/api/registries")
    async def registries_api() -> dict[str, Any]:
        groups = list_registry_groups()
        return {"count": len(groups), "registries": groups}

    @application.get("/api/registries/{registry_id}")
    async def registry_api(registry_id: str) -> dict[str, Any]:
        group = next(
            (item for item in list_registry_groups() if item["id"] == registry_id),
            None,
        )
        if group is None:
            raise HTTPException(status_code=404, detail="Unknown registry")
        return group

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
        if model_class is None:
            raise HTTPException(
                status_code=400,
                detail="This registry tool uses its workflow endpoint",
            )
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

    @application.post("/api/reactions/mine")
    async def mine_reaction(request: ReactionMiningRequest) -> dict[str, Any]:
        """Run the core ZymeForge reaction-to-enzyme workflow."""
        catalog_path = Path(
            os.getenv("ZYMEFORGE_CATALOG", str(REPOSITORY_DIR / "data" / "demo_catalog.json"))
        )
        if not catalog_path.exists():
            raise HTTPException(
                status_code=503,
                detail=f"ZymeForge catalog is not configured: {catalog_path}",
            )
        try:
            result = _workflow(str(catalog_path)).run(
                request.reaction,
                context=ReactionContext(ph=request.ph, temperature_c=request.temperature_c),
                top_k=request.top_k,
            )
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result.model_dump(mode="json")

    return application


app = create_app()
