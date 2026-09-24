"""FastAPI application for the ZymePage model catalog."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import tempfile
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError
from zymeforge.agent import AgentRequest, OpenAIResponsesProvider, RequestCompiler
from zymeforge.bootstrap import build_discovery_service, build_reaction_workflow
from zymeforge.core.models import ReactionContext
from zymeforge.engineer.mutate import UnZiproOptions, UnZiproProvider
from zymeforge.engineer.redesign import (
    LigandMPNNDesignOptions,
    LigandMPNNModelType,
    LigandMPNNProvider,
    LigandMPNNScoreOptions,
    MPNNScoringMode,
)
from zymeforge.function.adapters import ModelBackendUnavailable
from zymeforge.harness.factory import build_harness_runtime
from zymeforge.harness.run_store import RunStore
from zymeforge.harness.validator import PlanValidationError
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
from zymeforge.structure.active_site import compare_active_site
from zymeforge.structure.comparison import USAlignProvider
from zymeforge.structure.ligand_analysis import analyze_ligand
from zymeforge.structure.prediction import (
    AlphaFold3Provider,
    Boltz2Provider,
    ESMFoldProvider,
    StructurePredictionRequest,
)
from zymeforge.structure.quality import MolProbityProvider
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


class RedesignRequest(BaseModel):
    structure_pdb: str = Field(min_length=20)
    model_type: LigandMPNNModelType = LigandMPNNModelType.PROTEIN
    options: dict[str, Any] = Field(default_factory=dict)


class SequenceScoreRequest(BaseModel):
    structure_pdb: str = Field(min_length=20)
    sequence: str | None = Field(default=None, min_length=1)
    model_type: LigandMPNNModelType = LigandMPNNModelType.PROTEIN
    scoring_mode: MPNNScoringMode = MPNNScoringMode.SINGLE_AA
    options: dict[str, Any] = Field(default_factory=dict)


class MutationRequest(BaseModel):
    parent_id: str = Field(min_length=1)
    sequence: str = Field(min_length=1)
    structure_pdb: str = Field(min_length=20)
    top_k: int = Field(default=100, ge=1, le=1000)
    residue_map: dict[str, int] | None = None
    residues: str | None = None
    output_probabilities: bool = False
    output_logits: bool = False


class StructurePredictionAPIRequest(BaseModel):
    candidate_id: str = Field(default="query", min_length=1)
    method: str = Field(pattern="^(boltz2|alphafold3|esmfold)$")
    sequence: str = Field(min_length=1)
    additional_chains: dict[str, str] = Field(default_factory=dict)
    nucleic_acids: dict[str, str] = Field(default_factory=dict)
    ligand: str | None = None
    cofactors: list[str] = Field(default_factory=list)
    seed: int = Field(default=0, ge=0)
    options: dict[str, Any] = Field(default_factory=dict)


class StructureComparisonAPIRequest(BaseModel):
    query_structure: str = Field(min_length=20)
    target_structure: str = Field(min_length=20)
    query_id: str = "query"
    target_id: str = "target"


class ActiveSiteAPIRequest(StructureComparisonAPIRequest):
    catalytic_residues: list[str] = Field(min_length=2)
    pocket_residues: list[str] = Field(default_factory=list)


class LigandAnalysisAPIRequest(BaseModel):
    candidate_id: str = "query"
    structure: str = Field(min_length=20)
    ligand_id: str = Field(min_length=1)
    reference_structure: str | None = None
    external_metrics: dict[str, float] = Field(default_factory=dict)


class StructureQualityAPIRequest(BaseModel):
    candidate_id: str = "query"
    structure: str = Field(min_length=20)


class HarnessCompileRequest(BaseModel):
    query: str = Field(min_length=1, max_length=20_000)
    model: str | None = Field(default=None, min_length=1, max_length=100)


class HarnessRunRequest(BaseModel):
    query: str = Field(min_length=1, max_length=20_000)
    agent_request: AgentRequest


@lru_cache(maxsize=4)
def _workflow(catalog_path: str):
    return build_reaction_workflow(catalog_path)


@lru_cache(maxsize=4)
def _discovery(catalog_path: str):
    return build_discovery_service(catalog_path)


def _catalog_path() -> Path:
    return Path(os.getenv("ZYMEFORGE_CATALOG", str(REPOSITORY_DIR / "data" / "demo_catalog.json")))


def _harness_root() -> Path:
    return Path(os.getenv("ZYMEFORGE_HARNESS_RUNS", "/tmp/zymeforge-harness-runs"))


def _reject_harness_paths(request: AgentRequest) -> None:
    forbidden = {
        key
        for key in request.target
        if any(token in key.lower() for token in ("path", "file", "directory"))
    }
    if forbidden:
        raise ValueError(
            "server filesystem paths cannot be supplied: " + ", ".join(sorted(forbidden))
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


def _safe_engineering_options(options: dict[str, Any]) -> dict[str, Any]:
    path_options = {
        "bias_AA_per_residue",
        "omit_AA_per_residue",
    }
    forbidden = {
        key
        for key in options
        if "path" in key
        or "checkpoint" in key
        or key.endswith("_multi")
        or key in path_options
        or key in {"pdb", "pdbdir", "pdb_path", "out_folder", "outdir"}
    }
    if forbidden:
        raise ValueError(
            "server-managed path options cannot be supplied: " + ", ".join(sorted(forbidden))
        )
    return dict(options)


def _mpnn_checkpoint(model_type: LigandMPNNModelType) -> tuple[str, Path]:
    variable = {
        LigandMPNNModelType.PROTEIN: "ZYMEFORGE_PROTEIN_MPNN_CHECKPOINT",
        LigandMPNNModelType.LIGAND: "ZYMEFORGE_LIGAND_MPNN_CHECKPOINT",
        LigandMPNNModelType.SOLUBLE: "ZYMEFORGE_SOLUBLE_MPNN_CHECKPOINT",
        LigandMPNNModelType.GLOBAL_MEMBRANE: "ZYMEFORGE_GLOBAL_MEMBRANE_MPNN_CHECKPOINT",
        LigandMPNNModelType.PER_RESIDUE_MEMBRANE: (
            "ZYMEFORGE_PER_RESIDUE_MEMBRANE_MPNN_CHECKPOINT"
        ),
    }[model_type]
    field = {
        LigandMPNNModelType.PROTEIN: "checkpoint_protein_mpnn",
        LigandMPNNModelType.LIGAND: "checkpoint_ligand_mpnn",
        LigandMPNNModelType.SOLUBLE: "checkpoint_soluble_mpnn",
        LigandMPNNModelType.GLOBAL_MEMBRANE: "checkpoint_global_label_membrane_mpnn",
        LigandMPNNModelType.PER_RESIDUE_MEMBRANE: ("checkpoint_per_residue_label_membrane_mpnn"),
    }[model_type]
    return field, _configured_path(variable)


def _public_engineering_result(result: Any) -> dict[str, Any]:
    payload = result.model_dump(mode="json")
    payload["artifacts"] = []
    payload["input_structure"] = "staged-api-input"
    if "output_structure" in payload:
        payload["output_structure"] = None
    provenance = payload.get("provenance", {})
    provenance.pop("command", None)
    return payload


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
    docs_url = os.getenv("ZYMEFORGE_DOCS_URL", "https://gabriel-qin.github.io/ZymeForge_docs/")

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

    @application.get("/harness", response_class=HTMLResponse, include_in_schema=False)
    async def harness_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="harness.html",
            context={"docs_url": docs_url, "page": "harness"},
        )

    @application.post("/harness/compile", include_in_schema=False)
    @application.post("/api/harness/compile")
    async def compile_harness(request: HarnessCompileRequest) -> dict[str, Any]:
        try:
            provider = OpenAIResponsesProvider(
                model=request.model or os.getenv("ZYMEFORGE_LLM_MODEL", "gpt-6-astra")
            )
            compiled = RequestCompiler(provider).compile(request.query)
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return compiled.model_dump(mode="json")

    @application.post("/harness/run", include_in_schema=False)
    @application.post("/api/harness/run")
    async def run_harness(
        request: HarnessRunRequest, background_tasks: BackgroundTasks
    ) -> dict[str, Any]:
        try:
            _reject_harness_paths(request.agent_request)
            runtime = build_harness_runtime(_harness_root())
            runtime.validator.validate_or_raise(request.agent_request)
        except (ValueError, PlanValidationError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        run_id = f"harness_{uuid4().hex}"
        background_tasks.add_task(
            runtime.run,
            request.agent_request,
            user_query=request.query,
            run_id=run_id,
        )
        return {"run_id": run_id, "status": "PENDING"}

    @application.get("/harness/runs/{run_id}", include_in_schema=False)
    @application.get("/api/harness/runs/{run_id}")
    async def harness_run(run_id: str) -> dict[str, Any]:
        try:
            state = RunStore(_harness_root()).load(run_id)
        except (OSError, ValueError, ValidationError) as exc:
            raise HTTPException(status_code=404, detail="Unknown Harness run") from exc
        return {
            "run_id": state.run_id,
            "status": state.status,
            "current_step": state.current_step,
            "plan": state.resolved_plan,
            "completed_steps": state.completed_steps,
            "failed_steps": state.failed_steps,
            "candidate_count": len(state.candidates),
            "candidates": [item.model_dump(mode="json") for item in state.candidates],
            "results": {
                step: [result.model_dump(mode="json") for result in results]
                for step, results in state.results.items()
            },
            "missing_information": state.agent_request.missing_information,
            "error": state.error,
        }

    @application.get("/tools/{identifier}", response_class=HTMLResponse, include_in_schema=False)
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
                        index, manifest = load_index_bundle(_configured_path("ZYMEFORGE_DHR_INDEX"))
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

    @application.post("/api/engineering/redesign")
    async def redesign_sequence(request: RedesignRequest) -> dict[str, Any]:
        """Run official LigandMPNN with server-managed source and checkpoints."""
        try:
            source = _configured_path("ZYMEFORGE_LIGANDMPNN_SOURCE")
            checkpoint_field, checkpoint = _mpnn_checkpoint(request.model_type)
            values = _safe_engineering_options(request.options)
            with tempfile.TemporaryDirectory(prefix="zymeforge_redesign_") as temporary:
                work = Path(temporary)
                structure = work / "input.pdb"
                structure.write_text(request.structure_pdb, encoding="utf-8")
                values.update(
                    {
                        "pdb_path": structure,
                        "out_folder": work / "output",
                        "model_type": request.model_type,
                        checkpoint_field: checkpoint,
                    }
                )
                if values.get("pack_side_chains"):
                    values["checkpoint_path_sc"] = _configured_path(
                        "ZYMEFORGE_LIGANDMPNN_SIDECHAIN_CHECKPOINT"
                    )
                options = LigandMPNNDesignOptions(**values)
                results = LigandMPNNProvider(source).design_sequence(
                    structure, model_type=request.model_type, options=options
                )
                public_results = [_public_engineering_result(item) for item in results]
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except (OSError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "job_id": str(uuid4()),
            "status": "completed",
            "count": len(public_results),
            "designs": public_results,
        }

    @application.post("/api/engineering/score")
    async def score_sequence(request: SequenceScoreRequest) -> dict[str, Any]:
        """Run official LigandMPNN score.py on the sequence encoded in the submitted PDB."""
        try:
            source = _configured_path("ZYMEFORGE_LIGANDMPNN_SOURCE")
            checkpoint_field, checkpoint = _mpnn_checkpoint(request.model_type)
            values = _safe_engineering_options(request.options)
            with tempfile.TemporaryDirectory(prefix="zymeforge_score_") as temporary:
                work = Path(temporary)
                structure = work / "input.pdb"
                structure.write_text(request.structure_pdb, encoding="utf-8")
                values.update(
                    {
                        "pdb_path": structure,
                        "out_folder": work / "output",
                        "model_type": request.model_type,
                        "scoring_mode": request.scoring_mode,
                        checkpoint_field: checkpoint,
                    }
                )
                options = LigandMPNNScoreOptions(**values)
                results = LigandMPNNProvider(source).score_sequence_mpnn(
                    structure, request.sequence, options=options
                )
                public_results = [_public_engineering_result(item) for item in results]
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except (OSError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "job_id": str(uuid4()),
            "status": "completed",
            "count": len(public_results),
            "scores": public_results,
        }

    @application.post("/api/engineering/mutations")
    async def predict_mutations(request: MutationRequest) -> dict[str, Any]:
        """Run official unZipro; current upstream inference requires a structure."""
        try:
            source = _configured_path("ZYMEFORGE_UNZIPRO_SOURCE")
            parameter = _configured_path("ZYMEFORGE_UNZIPRO_CHECKPOINT")
            config = _configured_path("ZYMEFORGE_UNZIPRO_CONFIG")
            with tempfile.TemporaryDirectory(prefix="zymeforge_unzipro_") as temporary:
                work = Path(temporary)
                structure = work / "input.pdb"
                structure.write_text(request.structure_pdb, encoding="utf-8")
                options = UnZiproOptions(
                    pdb=structure,
                    gpu=int(os.getenv("ZYMEFORGE_ENGINEERING_GPU", "0")),
                    param=parameter,
                    config_path=config,
                    outdir=work / "output",
                    probs=request.output_probabilities,
                    logits=request.output_logits,
                    rank_by_prob=True,
                    res=request.residues,
                )
                results = UnZiproProvider(source).predict_mutations(
                    request.sequence,
                    parent_id=request.parent_id,
                    top_k=request.top_k,
                    options=options,
                    residue_map=request.residue_map,
                )
                public_results = [
                    {**item.model_dump(mode="json"), "artifacts": []} for item in results
                ]
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except (OSError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "job_id": str(uuid4()),
            "status": "completed",
            "count": len(public_results),
            "mutations": public_results,
        }

    @application.post("/api/structures/predict")
    async def predict_structure(request: StructurePredictionAPIRequest) -> dict[str, Any]:
        """Run a configured official structure provider without accepting server paths."""
        forbidden = sorted(
            key
            for key in request.options
            if "path" in key or "dir" in key or "cache" in key or "checkpoint" in key
        )
        if forbidden:
            raise HTTPException(
                status_code=422,
                detail="server-managed options cannot be supplied: " + ", ".join(forbidden),
            )
        try:
            with tempfile.TemporaryDirectory(prefix="zymeforge_structure_") as temporary:
                work = Path(temporary)
                prediction_request = StructurePredictionRequest(
                    candidate_id=request.candidate_id,
                    sequences={"A": request.sequence, **request.additional_chains},
                    nucleic_acids=request.nucleic_acids,
                    ligand_smiles=request.ligand,
                    cofactors=tuple(request.cofactors),
                    output_directory=work / "output",
                    seed=request.seed,
                    options=request.options,
                )
                if request.method == "boltz2":
                    provider = Boltz2Provider(os.getenv("ZYMEFORGE_BOLTZ_BINARY", "boltz"))
                elif request.method == "esmfold":
                    provider = ESMFoldProvider(_configured_path("ZYMEFORGE_ESMFOLD_CHECKPOINT"))
                else:
                    provider = AlphaFold3Provider(
                        _configured_path("ZYMEFORGE_AF3_SOURCE"),
                        _configured_path("ZYMEFORGE_AF3_MODEL_DIR"),
                        _configured_path("ZYMEFORGE_AF3_DATABASE_DIR"),
                    )
                result = provider.predict(prediction_request)
                structure_content = result.structure_file.read_text()
                public_result = result.model_dump(mode="json")
                public_result["structure_file"] = "inline"
                public_result["artifacts"] = []
                if public_result.get("pae_file"):
                    public_result["pae_file"] = "inline-result"
                public_result["provenance"].pop("command", None)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except (OSError, RuntimeError, ImportError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "job_id": str(uuid4()),
            "status": "completed",
            "result": public_result,
            "structure": structure_content,
        }

    @application.post("/api/structures/compare")
    async def compare_structures(request: StructureComparisonAPIRequest) -> dict[str, Any]:
        try:
            with tempfile.TemporaryDirectory(prefix="zymeforge_compare_") as temporary:
                work = Path(temporary)
                query = work / "query.pdb"
                target = work / "target.pdb"
                query.write_text(request.query_structure)
                target.write_text(request.target_structure)
                result = USAlignProvider(os.getenv("ZYMEFORGE_USALIGN_BINARY", "TMalign")).compare(
                    query,
                    target,
                    query_id=request.query_id,
                    target_id=request.target_id,
                )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return result.model_dump(mode="json")

    @application.post("/api/structures/active-site")
    async def analyze_active_site(request: ActiveSiteAPIRequest) -> dict[str, Any]:
        try:
            with tempfile.TemporaryDirectory(prefix="zymeforge_active_site_") as temporary:
                work = Path(temporary)
                query = work / "query.pdb"
                reference = work / "reference.pdb"
                query.write_text(request.query_structure)
                reference.write_text(request.target_structure)
                result = compare_active_site(
                    query,
                    reference,
                    tuple(request.catalytic_residues),
                    pocket_residues=tuple(request.pocket_residues),
                    query_id=request.query_id,
                    reference_id=request.target_id,
                )
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result.model_dump(mode="json")

    @application.post("/api/structures/ligand")
    async def analyze_structure_ligand(request: LigandAnalysisAPIRequest) -> dict[str, Any]:
        try:
            with tempfile.TemporaryDirectory(prefix="zymeforge_ligand_") as temporary:
                work = Path(temporary)
                structure = work / "query.pdb"
                structure.write_text(request.structure)
                reference = None
                if request.reference_structure:
                    reference = work / "reference.pdb"
                    reference.write_text(request.reference_structure)
                result = analyze_ligand(
                    structure,
                    request.ligand_id,
                    candidate_id=request.candidate_id,
                    reference_structure=reference,
                    external_metrics=request.external_metrics,
                )
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result.model_dump(mode="json")

    @application.post("/api/structures/quality")
    async def analyze_structure_quality(request: StructureQualityAPIRequest) -> dict[str, Any]:
        try:
            with tempfile.TemporaryDirectory(prefix="zymeforge_quality_") as temporary:
                structure = Path(temporary) / "query.pdb"
                structure.write_text(request.structure)
                result = MolProbityProvider(
                    os.getenv("ZYMEFORGE_MOLPROBITY_BINARY", "phenix.molprobity")
                ).analyze(structure, candidate_id=request.candidate_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return result.model_dump(mode="json")

    return application


app = create_app()
