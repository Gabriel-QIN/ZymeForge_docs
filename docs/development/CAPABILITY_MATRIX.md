# Capability matrix

Status meanings:

- **Runnable**: executes with built-in code or an installed dependency.
- **Guarded wrapper**: implementation exists and reports unavailable until its external
  binary, model asset, index, database, or license gate is configured.
- **Adapter**: normalized model contract exists; the upstream inference runner is not bound.

| Domain | Capability | Providers | Status |
|---|---|---|---|
| Reaction | exact/similar reaction, reaction-to-EC/enzyme | local catalog routes | Runnable |
| Reaction data | Rhea, EnzymeMap, M-CSA | versioned loaders with checksums | Runnable |
| Sequence | high-throughput alignment | MMseqs2 | Runnable when database is configured |
| Sequence | HMM/profile retrieval | phmmer, HHsearch | Guarded wrapper |
| Sequence/PLM | semantic and remote-homology retrieval | ESM-2, TM-Vec, DHR | Guarded wrapper |
| Multimodal | sequence/structure/text retrieval | SaProt, ProteinMPNN, ProTrek | Guarded wrapper |
| Structure search | direct structure retrieval and validation | Foldseek, US-align, DALI | Guarded wrapper |
| Active site | catalytic geometry and ligand/metal analysis | built-in geometry providers | Runnable |
| Pocket | detection and local comparison | fpocket, P2Rank, PocketMatch | Guarded wrapper |
| Function | EC, catalytic site, specificity, kinetics, pH, stability, solubility | Functional Prediction Registry V1 | Adapter |
| Structure prediction | monomer, complex and ligand-aware prediction | Boltz-2, AlphaFold 3, ESMFold | Guarded wrapper |
| Engineering | sequence redesign and scoring | LigandMPNN/ProteinMPNN | Guarded wrapper |
| Engineering | mutation prediction | unZipro, FoldX, GeoStab, ThermoMPNN | Guarded wrapper / Adapter |
| Fusion | weighted ZymeScore and rank fusion | weighted fusion, RRF | Runnable |
| Fusion | calibration and learned/multi-objective ranking | Platt, isotonic, logistic, Pareto | Runnable |
| Runtime | constrained plan execution and artifacts | Harness V1 | Runnable |
| Operations | dependency/asset/license/handler status | tool health API and CLI | Runnable |
| Benchmarking | retrieval, reaction and fusion definitions | versioned manifests | Runnable definitions; no claimed results |

Use the live health endpoint or CLI for machine-specific availability. A catalog card marked
as implemented does not imply that proprietary weights or a production database are present.
