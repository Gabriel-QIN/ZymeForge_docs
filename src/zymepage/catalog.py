"""Registry-backed metadata exposed by the ZymePage web catalog."""

from __future__ import annotations

from typing import Any

from zymeforge.engineer.mutate import MODELS as MUTATION_MODEL_PLUGINS
from zymeforge.function import MODEL_PLUGINS

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
        "role": card.role,
        "runtime": card.runtime,
        "inputs": list(card.input_fields),
        "outputs": list(card.output_fields),
        "capability": spec.capability,
        "available": False,
    }


def list_tools() -> list[dict[str, Any]]:
    """List every functional and mutation model registered by ZymeForge."""
    models = (*MODEL_PLUGINS, *MUTATION_MODEL_PLUGINS)
    return sorted((serialize_model(model) for model in models), key=lambda item: item["name"])


def get_tool(identifier: str) -> tuple[type[Any], dict[str, Any]] | None:
    """Resolve a catalog item and its model adapter class."""
    for model in (*MODEL_PLUGINS, *MUTATION_MODEL_PLUGINS):
        if tool_id(model) == identifier:
            return model, serialize_model(model)
    return None
