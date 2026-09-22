# Add a model

<!-- Adapter registration guide -->

For the complete registration guide—including database, search, engineering, workflow, and output plugins—see [Registering plugins in ZymeForge](https://github.com/Gabriel-QIN/ZymeForge/blob/master/src/zymeforge/registry/README.md).

Define an adapter class with a `PluginSpec` and `FunctionModelCard`, then expose it from the relevant domain package.

```python
from zymeforge.core.models import PluginSpec
from zymeforge.function.adapters import FunctionModelCard, UnifiedFunctionModel


class NewKineticsModel(UnifiedFunctionModel):
    spec = PluginSpec(
        name="new_kinetics",
        version="adapter-1.0",
        capability="prediction.kinetics",
        input_type="protein_sequence+substrate_smiles",
        output_type="kinetics_prediction",
        description="Kinetic parameter prediction adapter.",
    )
    card = FunctionModelCard(
        name="NewKinetics",
        task="kinetics_prediction",
        input_fields=("protein_sequence", "substrate_smiles"),
        output_fields=("kcat", "km", "kcat_per_km"),
        upstream="NewKinetics",
    )
```

Bind an in-process runner when constructing the adapter:

```python
model = NewKineticsModel(
    runner=predict_kinetics,
    model_path="weights/new-kinetics",
    device="cuda",
)
predictions = model.predict({
    "protein_sequence": "MKT...",
    "substrate_smiles": "CCO",
})
```

The runner must return `FunctionalPrediction` objects or mappings accepted by that contract. Missing runners raise `ModelBackendUnavailable`.
