# Current architecture

ZymeForge is a registry-based enzyme discovery and engineering platform. Scientific
providers attach to shared `Candidate`, evidence, structure, and provenance contracts;
missing binaries, checkpoints, indexes, databases, or license acceptance are reported as
unavailable and never replaced by generated placeholder results.

```text
Reaction / substrate / protein / structure
                    ↓
     Exact, alignment, embedding and structure retrieval
                    ↓
      Function, site, pocket and kinetics evidence
                    ↓
       Calibrated fusion and candidate ranking
                    ↓
       Mutation prediction or sequence redesign
                    ↓
          Structure and ligand validation
```

## Implemented provider families

| Area | Implemented interfaces and providers |
|---|---|
| Reaction data | local catalog, versioned Rhea, EnzymeMap and M-CSA ingestion |
| Reaction mining | exact lookup, similarity baseline, reaction-to-EC, direct reaction-to-enzyme |
| Sequence retrieval | MMseqs2, phmmer, HHsearch, ESM-2, TM-Vec and DHR |
| Multimodal retrieval | SaProt, ProteinMPNN encoder and ProTrek sequence/text/structure modes |
| Structure retrieval | Foldseek, US-align/TM-align and DALI validation |
| Active site and pocket | catalytic geometry, ligand/metal geometry, fpocket, P2Rank and PocketMatch |
| Structure prediction | Boltz-2, AlphaFold 3 and ESMFold guarded wrappers |
| Engineering | LigandMPNN/ProteinMPNN redesign, unZipro and FoldX plus mutation model adapters |
| Evidence fusion | weighted ZymeScore, reciprocal rank fusion, Platt/isotonic calibration, Pareto and logistic ranking |
| Runtime | constrained Harness V1, deterministic routing, run artifacts and tool health reports |

An implemented wrapper is not automatically an available installation. The Registry page
shows the distinction, while `zymeforge harness health --json` reports the current machine.

## Runtime and provenance

Harness V1 compiles or accepts one validated plan and executes only registered handlers.
It has no reflection loop, dynamic replanning, autonomous shell access, or multi-agent
execution. Each tool result stores parameters, timestamps, elapsed time, tool version,
runtime information, artifacts, normalized candidates, and provider provenance.

The unified environment uses Python 3.11, official package sources, CUDA 12.8-compatible
PyTorch, and one `zymeforge` Conda environment. Restricted providers such as local
AlphaFold 3 remain disabled until legal model parameters and license gates are configured.
