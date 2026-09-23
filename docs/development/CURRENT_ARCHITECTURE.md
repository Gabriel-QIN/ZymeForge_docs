# Current Architecture

This document records the implemented repository state. It distinguishes runnable code from adapter metadata and planned capabilities.

## Platform boundary

ZymeForge is currently an automated enzyme discovery and engineering platform. It does not contain an LLM planner, autonomous tool router, critic, reflection loop, dynamic replanning, multi-agent runtime, or Harness.

```text
Input and normalization
        ↓
Typed provider registries
        ↓
Discovery and fixed workflows
        ↓
Evidence fusion and ranking
        ↓
Engineering contracts and output writers
```

## Implemented packages

| Package | Current responsibility | Implementation state |
|---|---|---|
| `core` | stable records, `Candidate`, `ToolResult`, provenance, evidence, score cards | implemented |
| `input_data` | reaction parsing and lexical reaction-SMILES normalization | runnable baseline |
| `database` | versioned local reaction/protein catalog | runnable baseline |
| `substrate` | SMILES/InChI/InChIKey/name query contract and substrate-to-enzyme provider | runnable local-catalog baseline |
| `reaction` | reaction input types and backward-compatible reaction imports | implemented |
| `search.reaction` | exact, lexical-similarity, reaction-to-EC, and reaction-to-enzyme routes | runnable local-catalog baseline |
| `search.sequence_based` | sequence-search protocol and registry | contract only |
| `search.structure_based` | structure-search protocol and registry | contract only |
| `function` | normalized function prediction runtime and model cards | contracts and adapters; upstream runners not bound |
| `structure_prediction` | normalized structure prediction result and provider protocol | contract only |
| `engineer.mutate` | mutation contracts plus GeoStab/ThermoMPNN adapters | adapters only; upstream runners not bound |
| `engineer.redesign` | redesign contract and registry | contract only |
| `fusion` | weighted calibrated evidence fusion | runnable |
| `workflow` | reaction-mining workflow and YAML definition validation | runnable fixed workflow |
| `output` | JSON and candidate TSV serialization | runnable |
| `registry` | generic kernel and capability-scoped registries | runnable |

## Runnable discovery paths

### Reaction SMILES

`build_reaction_workflow()` standardizes the query and runs four independent retrieval routes. Linked proteins are merged by protein identity, converted to evidence records, fused into `ScoreCard`, and ranked.

```text
reaction SMILES
  ├─ exact local reaction lookup
  ├─ lexical n-gram similarity
  ├─ catalog reaction → EC
  └─ catalog reaction → enzyme
          ↓
 CandidateReactionPair + EvidenceRecord
          ↓
       ZymeScore
```

The lexical similarity provider is a dependency-light baseline, not a chemistry-aware DRFP/RXNFP/CGR implementation.

### Substrate and general reaction queries

`build_discovery_service()` exposes stable methods:

```python
predict_enzymes_from_substrate()
predict_enzymes_from_reaction()
search_enzymes_by_reaction()
```

The local provider accepts substrate SMILES, InChI, InChIKey, or names when those identifiers are represented in the catalog. Reaction queries accept reaction SMILES, `substrate -> product`, EC numbers, names, and descriptions. The demo catalog currently contains enough annotations for SMILES, EC, and reaction-name examples; broader identifier resolution requires production databases.

## Identity and result contracts

`ProteinRecord.id` remains the stable protein identity. `Candidate.candidate_id` is derived as `candidate:<protein_id>` so retrieval routes do not create incompatible identifiers. Designed variants carry `parent_candidate_id`.

`ToolResult[T]` is the common result envelope for future providers and workflows. It records status, tool and version, normalized input/output, scores, files, parameters, runtime, error, and a `ProvenanceRecord`.

## Function adapter status

The repository registers 21 function adapters covering EC/function, catalytic sites, substrate compatibility, kinetics, pH, thermostability, solubility, cofactor preference, and developability. GeoStab and ThermoMPNN are registered for mutation effects.

These adapters share `FunctionalPrediction` and `UnifiedFunctionModel`, but registration does not mean inference is installed. Without an explicitly configured upstream runner and checkpoint, adapters raise `ModelBackendUnavailable` and never return fabricated predictions.

## Environment and reproducibility

- one `zymeforge` Conda environment;
- Python 3.11 for the CUDA environment;
- official PyPI and official PyTorch CUDA 12.8 wheel index;
- `torch==2.11.0+cu128` in the environment definition;
- RDKit from conda-forge;
- plugin, model, database, parameters, IDs, and timestamps available through provenance contracts.

## Tested behavior

The test suite covers registries, reaction normalization, reaction mining, discovery queries, function adapter behavior, fusion, output writers, workflow validation, candidate identity, and provenance serialization.
