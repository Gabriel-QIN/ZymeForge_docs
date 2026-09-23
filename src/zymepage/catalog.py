"""Registry-backed metadata exposed by the ZymePage web catalog."""

from __future__ import annotations

from typing import Any

from zymeforge.engineer.mutate import MODELS as MUTATION_MODEL_PLUGINS
from zymeforge.function import MODEL_PLUGINS

REGISTRY_GROUPS = (
    {
        "id": "reaction-mining",
        "label": "Reaction Mining",
        "registries": (
            "reaction_database", "reaction_encoder", "reaction_search",
            "reaction2ec", "reaction2enzyme", "substrate2enzyme",
        ),
        "intro": (
            "Start from substrates, products, reaction SMILES, EC numbers, or names "
            "and retrieve enzyme candidates."
        ),
    },
    {
        "id": "sequence-search",
        "label": "Sequence Search",
        "registries": ("sequence_search",),
        "intro": (
            "Search sequence space with alignment, profile, and protein language model "
            "evidence."
        ),
    },
    {
        "id": "structure-search",
        "label": "Structure Search",
        "registries": ("structure_search", "active_site_search"),
        "intro": (
            "Compare global folds and local catalytic geometry to recover remote enzyme "
            "relationships."
        ),
    },
    {
        "id": "function-prediction",
        "label": "Function Prediction",
        "registries": (
            "function_predictor", "substrate_compatibility", "kinetics_predictor",
            "stability_predictor", "ph_predictor", "solubility_predictor",
            "localization_predictor", "expression_predictor",
            "cofactor_predictor", "developability_predictor", "docking",
        ),
        "intro": (
            "Profile EC function, catalytic sites, substrate compatibility, kinetics, "
            "stability, and developability."
        ),
    },
    {
        "id": "structure-prediction",
        "label": "Structure Prediction",
        "registries": ("structure_predictor",),
        "intro": (
            "Generate protein and complex structures for pocket inspection, docking, "
            "and consistency checks."
        ),
    },
    {
        "id": "engineering",
        "label": "Engineering",
        "registries": (
            "mutation_site_selector", "mutation_generator", "mutation_predictor",
            "mutation_optimizer", "design_model",
        ),
        "intro": (
            "Move from a selected enzyme to targeted mutation optimization or sequence "
            "redesign."
        ),
    },
    {
        "id": "evidence-fusion",
        "label": "Evidence Fusion",
        "registries": ("evidence_provider", "score_calibrator", "fusion_model"),
        "intro": (
            "Calibrate heterogeneous evidence into an explainable ZymeScore and candidate ranking."
        ),
    },
    {
        "id": "output",
        "label": "Output",
        "registries": ("output_writer",),
        "intro": (
            "Export candidates, evidence, score cards, and provenance for downstream "
            "analysis."
        ),
    },
)

REGISTRY_BY_CAPABILITY = {
    "prediction.function": "function_predictor",
    "active_site.search": "active_site_search",
    "prediction.substrate_compatibility": "substrate_compatibility",
    "prediction.kinetics": "kinetics_predictor",
    "prediction.stability": "stability_predictor",
    "prediction.ph": "ph_predictor",
    "prediction.solubility": "solubility_predictor",
    "prediction.localization": "localization_predictor",
    "prediction.expression": "expression_predictor",
    "prediction.cofactor": "cofactor_predictor",
    "prediction.developability": "developability_predictor",
    "prediction.docking": "docking",
    "engineering.mutation.predictor": "mutation_predictor",
    "engineering.redesign": "design_model",
}

TASK_LABELS = {
    "ec_prediction": "EC & function",
    "catalytic_site_prediction": "Catalytic site",
    "substrate_compatibility": "Substrate specificity",
    "kinetics_prediction": "Kinetics",
    "ph_prediction": "Optimal pH",
    "thermostability_prediction": "Thermostability",
    "solubility_prediction": "Solubility",
    "cofactor_prediction": "Cofactor specificity",
    "signal_peptide_prediction": "Developability",
    "transmembrane_prediction": "Developability",
    "localization_prediction": "Developability",
    "mutation_effect_prediction": "Mutation effects",
}

TASK_INTROS = {
    "reaction_mining": (
        "Search exact and similar reactions, infer EC classes, and rank enzyme candidates."
    ),
    "ec_prediction": "Predict EC numbers and enzyme function from a protein sequence.",
    "catalytic_site_prediction": "Identify residues and local geometry that support catalysis.",
    "substrate_compatibility": "Estimate whether a candidate enzyme can accept a target substrate.",
    "kinetics_prediction": "Estimate catalytic parameters for an enzyme-substrate pair.",
    "ph_prediction": "Predict the pH optimum for enzyme activity.",
    "thermostability_prediction": "Estimate melting temperature or thermostability probability.",
    "solubility_prediction": "Estimate whether a protein is likely to remain soluble.",
    "cofactor_prediction": "Predict cofactor preference such as NAD, NADP, or FAD.",
    "signal_peptide_prediction": "Detect signal peptides and likely cleavage sites.",
    "transmembrane_prediction": "Detect transmembrane regions and topology.",
    "localization_prediction": "Predict cellular localization for developability triage.",
    "mutation_effect_prediction": "Estimate stability and fitness effects of a proposed mutation.",
}

WORKFLOW_TOOLS = (
    {
        "id": "substrate-to-enzyme--mining",
        "name": "Substrate-to-Enzyme Mining",
        "plugin": "substrate_discovery",
        "version": "workflow-1.0",
        "task": "reaction_mining",
        "category": "Reaction mining",
        "introduction": (
            "Resolve SMILES, InChI, InChIKey, or names and retrieve linked enzymes."
        ),
        "description": (
            "Runs the configured substrate-to-enzyme provider and returns normalized "
            "candidate, EC, reaction, confidence, source, and provenance fields."
        ),
        "role": "primary",
        "runtime": "zymeforge-unified",
        "inputs": ["query"],
        "outputs": ["candidate_enzymes", "predicted_ec", "confidence", "provenance"],
        "capability": "substrate.to_enzyme",
        "registry": "substrate2enzyme",
        "requires_gpu": False,
        "citation": None,
        "license": "Apache-2.0",
        "available": True,
        "kind": "workflow",
        "endpoint": "/api/substrates/mine",
    },
    {
        "id": "reaction-to-enzyme--mining",
        "name": "Reaction-to-Enzyme Mining",
        "plugin": "reaction_mining",
        "version": "workflow-1.0",
        "task": "reaction_mining",
        "category": "Reaction mining",
        "introduction": TASK_INTROS["reaction_mining"],
        "description": (
            "Runs the ZymeForge reaction standardizer, exact search, similarity search, "
            "reaction-to-EC, direct reaction-to-enzyme retrieval, and evidence fusion workflow."
        ),
        "role": "primary",
        "runtime": "zymeforge-unified",
        "inputs": ["reaction"],
        "outputs": ["ranked_candidates", "evidence", "zyme_score"],
        "capability": "reaction.to_enzyme",
        "registry": "reaction2enzyme",
        "requires_gpu": False,
        "citation": None,
        "license": "Apache-2.0",
        "available": True,
        "kind": "workflow",
        "endpoint": "/api/reactions/mine",
    },
)

SIMILARITY_TOOLS = (
    {
        "id": "esm2--similarity-retrieval",
        "name": "ESM-2 Retrieval",
        "plugin": "esm2_650m",
        "version": "1.0.0",
        "task": "protein_similarity",
        "category": "Sequence search",
        "introduction": "Retrieve proteins by ESM-2 sequence-semantic similarity.",
        "description": "Batched 650M embeddings, content cache, and Flat/HNSW retrieval.",
        "role": "primary",
        "runtime": "zymeforge-unified",
        "inputs": ["sequence"],
        "outputs": ["similarity_hits"],
        "capability": "sequence.search",
        "registry": "sequence_search",
        "requires_gpu": True,
        "citation": None,
        "license": "Apache-2.0",
        "available": False,
        "kind": "retrieval",
        "endpoint": "/api/similarity/search",
    },
    {
        "id": "saprot--similarity-retrieval",
        "name": "SaProt Retrieval",
        "plugin": "saprot_650m",
        "version": "1.0.0",
        "task": "protein_similarity",
        "category": "Structure search",
        "introduction": "Retrieve proteins using amino-acid and 3Di structural context.",
        "description": "Structure-aware SaProt embeddings with explicit structure provenance.",
        "role": "primary",
        "runtime": "zymeforge-unified",
        "inputs": ["sequence", "structural_tokens"],
        "outputs": ["similarity_hits"],
        "capability": "structure.search",
        "registry": "structure_search",
        "requires_gpu": True,
        "citation": None,
        "license": "Apache-2.0",
        "available": False,
        "kind": "retrieval",
        "endpoint": "/api/similarity/search",
    },
    {
        "id": "proteinmpnn--similarity-retrieval",
        "name": "ProteinMPNN Encoder Retrieval",
        "plugin": "proteinmpnn_encoder_experimental",
        "version": "1.0.0",
        "task": "protein_similarity",
        "category": "Structure search",
        "introduction": "Experimental retrieval from final ProteinMPNN backbone encoder states.",
        "description": "Chain-level, mean-pooled 128D backbone representation.",
        "role": "experimental",
        "runtime": "zymeforge-unified",
        "inputs": ["structure_pdb"],
        "outputs": ["similarity_hits"],
        "capability": "structure.search",
        "registry": "structure_search",
        "requires_gpu": True,
        "citation": None,
        "license": "Apache-2.0",
        "available": False,
        "kind": "retrieval",
        "endpoint": "/api/similarity/search",
    },
    {
        "id": "foldseek--similarity-retrieval",
        "name": "Foldseek Retrieval",
        "plugin": "foldseek",
        "version": "adapter-1.0",
        "task": "protein_similarity",
        "category": "Structure search",
        "introduction": "Search structures by 3Di and amino-acid local alignment.",
        "description": "Preserves identity, coverage, E-value, bit score, TM-scores, and lDDT.",
        "role": "primary",
        "runtime": "external-binary",
        "inputs": ["structure_pdb"],
        "outputs": ["similarity_hits"],
        "capability": "structure.search",
        "registry": "structure_search",
        "requires_gpu": False,
        "citation": None,
        "license": "Apache-2.0",
        "available": False,
        "kind": "retrieval",
        "endpoint": "/api/similarity/search",
    },
    {
        "id": "dali--structural-validation",
        "name": "DALI Validation",
        "plugin": "dali",
        "version": "adapter-1.0",
        "task": "structural_validation",
        "category": "Structure search",
        "introduction": "Validate only the top retrieved structures using DALI Z-scores.",
        "description": "Returns Z-score, RMSD, aligned length, identity, and protein lengths.",
        "role": "validation",
        "runtime": "external-binary",
        "inputs": ["structure_pdb", "candidate_structures"],
        "outputs": ["dali_results"],
        "capability": "structure.search",
        "registry": "structure_search",
        "requires_gpu": False,
        "citation": None,
        "license": "Apache-2.0",
        "available": False,
        "kind": "retrieval",
        "endpoint": "/api/similarity/search",
    },
)


def tool_id(model: type[Any]) -> str:
    """Return a stable URL identifier for a registered model/task pair."""
    return f"{model.spec.name}--{model.card.task}".replace("_", "-")


def serialize_model(model: type[Any]) -> dict[str, Any]:
    """Convert an adapter class into browser-safe catalog metadata."""
    card = model.card
    spec = model.spec
    return {
        "id": tool_id(model),
        "name": card.name,
        "plugin": spec.name,
        "version": spec.version,
        "task": card.task,
        "category": TASK_LABELS.get(card.task, card.task.replace("_", " ").title()),
        "description": spec.description,
        "introduction": TASK_INTROS.get(card.task, spec.description),
        "role": card.role,
        "runtime": card.runtime,
        "inputs": list(card.input_fields),
        "outputs": list(card.output_fields),
        "capability": spec.capability,
        "registry": REGISTRY_BY_CAPABILITY.get(spec.capability, spec.capability),
        "requires_gpu": spec.requires_gpu,
        "citation": spec.citation,
        "license": spec.license,
        "available": False,
        "kind": "model",
        "endpoint": f"/api/models/{tool_id(model)}/predict",
    }


def list_tools() -> list[dict[str, Any]]:
    """List every functional and mutation model registered by ZymeForge."""
    models = (*MODEL_PLUGINS, *MUTATION_MODEL_PLUGINS)
    return sorted(
        [*WORKFLOW_TOOLS, *SIMILARITY_TOOLS, *(serialize_model(model) for model in models)],
        key=lambda item: item["name"],
    )


def list_models() -> list[dict[str, Any]]:
    """List model adapters without workflow tools."""
    return [tool for tool in list_tools() if tool["kind"] == "model"]


def list_registry_groups() -> list[dict[str, Any]]:
    """Return Proto-style registry navigation with the currently registered tools."""
    tools = list_tools()
    groups: list[dict[str, Any]] = []
    for group in REGISTRY_GROUPS:
        registries = set(group["registries"])
        group_tools = [tool for tool in tools if tool["registry"] in registries]
        groups.append({**group, "tools": group_tools, "count": len(group_tools)})
    return groups


def get_tool(identifier: str) -> tuple[type[Any] | None, dict[str, Any]] | None:
    """Resolve a catalog item and its model adapter class."""
    for tool in list_tools():
        if tool["id"] == identifier:
            if tool["kind"] in {"workflow", "retrieval"}:
                return None, tool
            for model in (*MODEL_PLUGINS, *MUTATION_MODEL_PLUGINS):
                if tool_id(model) == identifier:
                    return model, tool
    return None
