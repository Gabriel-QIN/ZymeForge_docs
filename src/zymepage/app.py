"""FastAPI application for the ZymePage model catalog."""

from __future__ import annotations

import importlib
import json
import os
import tempfile
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from zymeforge.bootstrap import build_discovery_service, build_reaction_workflow
from zymeforge.core.models import ReactionContext
from zymeforge.function.adapters import ModelBackendUnavailable
from zymeforge.reaction import ReactionInputType
from zymeforge.similarity.dhr import DHREmbeddingExtractor, DHRSimilaritySearch
from zymeforge.similarity.esm2 import ESM2EmbeddingExtractor, ESM2SimilaritySearch
from zymeforge.similarity.foldseek import FoldseekRunner
from zymeforge.similarity.indexing import load_index_bundle
from zymeforge.similarity.merge import merge_similarity_hits
from zymeforge.similarity.proteinmpnn import (
    ProteinMPNNEmbeddingExtractor,
    ProteinMPNNSimilaritySearch,
    parse_pdb_backbones,
)
from zymeforge.similarity.protrek import (
    ProTrekEmbeddingExtractor,
    ProTrekModality,
    ProTrekSimilaritySearch,
)
from zymeforge.similarity.saprot import SaProtEmbeddingExtractor, SaProtSimilaritySearch
from zymeforge.similarity.schemas import SimilarityMethod
from zymeforge.similarity.tmvec import TMVecEmbeddingExtractor, TMVecSimilaritySearch
from zymeforge.similarity.validation.dali import DaliRunner
from zymeforge.substrate import SubstrateInputType

from zymepage.catalog import get_tool, list_models, list_registry_groups, list_tools

PACKAGE_DIR = Path(__file__).parent
REPOSITORY_DIR = PACKAGE_DIR.parents[1]


class ReactionMiningRequest(BaseModel):
    """Validated public request for the ZymeForge reaction mining workflow."""

    reaction: str = Field(min_length=3, description="Reaction SMILES: substrates>>products")
    top_k: int = Field(default=20, ge=1, le=1000)
    ph: float | None = Field(default=None, ge=0.0, le=14.0)
    temperature_c: float | None = None


class SubstrateDiscoveryRequest(BaseModel):
    query: str = Field(min_length=1, description="SMILES, InChI, InChIKey, or name")
    input_type: SubstrateInputType = SubstrateInputType.AUTO
    top_k: int = Field(default=20, ge=1, le=1000)


class ReactionDiscoveryRequest(BaseModel):
    query: str = Field(min_length=1, description="Reaction SMILES, EC, name, or description")
    input_type: ReactionInputType = ReactionInputType.AUTO
    top_k: int = Field(default=20, ge=1, le=1000)


class SimilaritySearchRequest(BaseModel):
    query_id: str = Field(default="query", min_length=1)
    sequence: str | None = Field(default=None, min_length=1)
    structure_pdb: str | None = Field(default=None, min_length=1)
    structural_tokens: str | None = Field(default=None, min_length=1)
    text: str | None = Field(default=None, min_length=1)
    methods: list[SimilarityMethod] = Field(default_factory=lambda: [SimilarityMethod.ESM2])
    protrek_query_type: ProTrekModality = ProTrekModality.SEQUENCE
    protrek_target_modality: ProTrekModality = ProTrekModality.SEQUENCE
    top_k: int = Field(default=100, ge=1, le=1000)
    dali_top_n: int = Field(default=0, ge=0, le=100)
    use_rrf: bool = False


@lru_cache(maxsize=4)
def _workflow(catalog_path: str):
    return build_reaction_workflow(catalog_path)


@lru_cache(maxsize=4)
def _discovery(catalog_path: str):
    return build_discovery_service(catalog_path)


def _catalog_path() -> Path:
    return Path(
        os.getenv("ZYMEFORGE_CATALOG", str(REPOSITORY_DIR / "data" / "demo_catalog.json"))
    )


def _configured_path(name: str) -> Path:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not configured on this deployment")
    path = Path(value)
    if not path.exists():
        raise RuntimeError(f"{name} does not exist: {path}")
    return path


def _configured_runner() -> Callable | None:
    value = os.getenv("ZYMEFORGE_PROTEINMPNN_RUNNER")
    if not value:
        return None
    module, separator, attribute = value.partition(":")
    if not separator:
        raise RuntimeError("ZYMEFORGE_PROTEINMPNN_RUNNER must use module:function")
    runner = getattr(importlib.import_module(module), attribute)
    if not callable(runner):
        raise RuntimeError("configured ProteinMPNN runner is not callable")
    return runner


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
        catalog_path = _catalog_path()
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

    @application.post("/api/substrates/mine")
    async def mine_substrate(request: SubstrateDiscoveryRequest) -> dict[str, Any]:
        """Run substrate-to-enzyme discovery using the configured provider."""
        catalog_path = _catalog_path()
        if not catalog_path.exists():
            raise HTTPException(status_code=503, detail="ZymeForge catalog is not configured")
        predictions = _discovery(str(catalog_path)).predict_enzymes_from_substrate(
            request.query,
            input_type=request.input_type,
            limit=request.top_k,
        )
        return {
            "query": request.query,
            "input_type": request.input_type,
            "count": len(predictions),
            "candidates": [item.model_dump(mode="json") for item in predictions],
        }

    @application.post("/api/reactions/discover")
    async def discover_reaction(request: ReactionDiscoveryRequest) -> dict[str, Any]:
        """Discover enzymes from reaction SMILES, EC, name, or description."""
        catalog_path = _catalog_path()
        if not catalog_path.exists():
            raise HTTPException(status_code=503, detail="ZymeForge catalog is not configured")
        try:
            predictions = _discovery(str(catalog_path)).predict_enzymes_from_reaction(
                request.query,
                input_type=request.input_type,
                limit=request.top_k,
            )
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "query": request.query,
            "input_type": request.input_type,
            "count": len(predictions),
            "candidates": [item.model_dump(mode="json") for item in predictions],
        }

    @application.post("/similarity/search", include_in_schema=False)
    @application.post("/api/similarity/search")
    async def search_similarity(request: SimilaritySearchRequest) -> dict[str, Any]:
        """Run configured similarity providers; missing scientific assets return 503."""
        if not request.methods:
            raise HTTPException(status_code=422, detail="At least one retrieval method is required")
        if SimilarityMethod.DALI in request.methods:
            raise HTTPException(
                status_code=422,
                detail="DALI is selected with dali_top_n, not as a retrieval method",
            )
        device = os.getenv("ZYMEFORGE_SIMILARITY_DEVICE")
        try:
            with tempfile.TemporaryDirectory(prefix="zymeforge_similarity_") as temporary:
                temporary_path = Path(temporary)
                structure = None
                if request.structure_pdb:
                    structure = temporary_path / "query.pdb"
                    structure.write_text(request.structure_pdb, encoding="utf-8")
                hits: dict[SimilarityMethod, list] = {}
                for method in request.methods:
                    if method == SimilarityMethod.ESM2:
                        if request.sequence is None:
                            raise ValueError("ESM-2 requires sequence")
                        index, manifest = load_index_bundle(
                            _configured_path("ZYMEFORGE_ESM2_INDEX")
                        )
                        adapter = ESM2SimilaritySearch(
                            extractor=ESM2EmbeddingExtractor(device=device),
                            index=index,
                            index_name=manifest.name,
                            index_version=manifest.index_version,
                        )
                        hits[method] = adapter.search_sequence(
                            request.query_id, request.sequence, top_k=request.top_k
                        )
                    elif method == SimilarityMethod.TMVEC:
                        if request.sequence is None:
                            raise ValueError("TM-Vec requires sequence")
                        index, manifest = load_index_bundle(
                            _configured_path("ZYMEFORGE_TMVEC_INDEX")
                        )
                        adapter = TMVecSimilaritySearch(
                            TMVecEmbeddingExtractor(
                                checkpoint=_configured_path("ZYMEFORGE_TMVEC_CHECKPOINT"),
                                device=device,
                            ),
                            index,
                            index_name=manifest.name,
                            index_backend=manifest.backend,
                        )
                        hits[method] = adapter.search_sequence(
                            request.query_id, request.sequence, top_k=request.top_k
                        )
                    elif method == SimilarityMethod.DHR:
                        if request.sequence is None:
                            raise ValueError("DHR requires sequence")
                        index, manifest = load_index_bundle(
                            _configured_path("ZYMEFORGE_DHR_INDEX")
                        )
                        adapter = DHRSimilaritySearch(
                            DHREmbeddingExtractor(
                                checkpoint_directory=_configured_path(
                                    "ZYMEFORGE_DHR_CHECKPOINT_DIR"
                                ),
                                device=device,
                            ),
                            index,
                            index_name=manifest.name,
                        )
                        hits[method] = adapter.search_sequence(
                            request.query_id, request.sequence, top_k=request.top_k
                        )
                    elif method == SimilarityMethod.PROTREK:
                        index, manifest = load_index_bundle(
                            _configured_path("ZYMEFORGE_PROTREK_INDEX")
                        )
                        modality = request.protrek_query_type
                        if modality == ProTrekModality.SEQUENCE:
                            if request.sequence is None:
                                raise ValueError("ProTrek sequence query requires sequence")
                            protrek_query: str | Path = request.sequence
                        elif modality == ProTrekModality.TEXT:
                            if request.text is None:
                                raise ValueError("ProTrek text query requires text")
                            protrek_query = request.text
                        else:
                            if structure is None:
                                raise ValueError("ProTrek structure query requires structure_pdb")
                            protrek_query = structure
                        configured_checkpoint = os.getenv("ZYMEFORGE_PROTREK_CHECKPOINT")
                        adapter = ProTrekSimilaritySearch(
                            ProTrekEmbeddingExtractor(
                                source_directory=_configured_path("ZYMEFORGE_PROTREK_SOURCE"),
                                weights_directory=_configured_path("ZYMEFORGE_PROTREK_WEIGHTS"),
                                checkpoint=configured_checkpoint,
                                device=device,
                            ),
                            index,
                            target_modality=request.protrek_target_modality,
                            index_name=manifest.name,
                        )
                        hits[method] = adapter.search(
                            protrek_query,
                            query_type=modality,
                            query_id=request.query_id,
                            top_k=request.top_k,
                        )
                    elif method == SimilarityMethod.SAPROT:
                        if request.sequence is None or request.structural_tokens is None:
                            raise ValueError("SaProt requires sequence and structural_tokens")
                        index, _ = load_index_bundle(_configured_path("ZYMEFORGE_SAPROT_INDEX"))
                        hits[method] = SaProtSimilaritySearch(
                            SaProtEmbeddingExtractor(device=device), index
                        ).search(
                            request.query_id,
                            request.sequence,
                            request.structural_tokens,
                            structure_source="api",
                            structure_id=request.query_id,
                            top_k=request.top_k,
                        )
                    elif method == SimilarityMethod.PROTEINMPNN:
                        if structure is None:
                            raise ValueError("ProteinMPNN retrieval requires structure_pdb")
                        index, _ = load_index_bundle(
                            _configured_path("ZYMEFORGE_PROTEINMPNN_INDEX")
                        )
                        extractor = ProteinMPNNEmbeddingExtractor(runner=_configured_runner())
                        hits[method] = ProteinMPNNSimilaritySearch(extractor, index).search(
                            parse_pdb_backbones(structure, structure_source="api")[0],
                            top_k=request.top_k,
                        )
                    elif method == SimilarityMethod.FOLDSEEK:
                        if structure is None:
                            raise ValueError("Foldseek retrieval requires structure_pdb")
                        hits[method] = FoldseekRunner().search(
                            structure,
                            database=_configured_path("ZYMEFORGE_FOLDSEEK_DATABASE"),
                            output_path=temporary_path / "foldseek.tsv",
                            temporary_directory=temporary_path / "foldseek_work",
                            limit=request.top_k,
                        )
                candidates = merge_similarity_hits(
                    (hit for method_hits in hits.values() for hit in method_hits),
                    use_rrf=request.use_rrf,
                )
                dali_results = []
                if request.dali_top_n:
                    if structure is None:
                        raise ValueError("DALI validation requires structure_pdb")
                    structure_root = _configured_path("ZYMEFORGE_CANDIDATE_STRUCTURE_DIR")
                    structures = {
                        item.target_id: structure_root / f"{Path(item.target_id).name}.pdb"
                        for item in candidates[: request.dali_top_n]
                        if (structure_root / f"{Path(item.target_id).name}.pdb").exists()
                    }
                    dali_results = DaliRunner().validate_top_n(
                        structure,
                        candidates,
                        structures,
                        query_id=request.query_id,
                        top_n=request.dali_top_n,
                    )
        except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "job_id": str(uuid4()),
            "status": "completed",
            "results": {
                "methods": {
                    method.value: [hit.model_dump(mode="json") for hit in method_hits]
                    for method, method_hits in hits.items()
                },
                "candidates": [item.model_dump(mode="json") for item in candidates],
                "dali": [item.model_dump(mode="json") for item in dali_results],
            },
        }

    return application


app = create_app()
