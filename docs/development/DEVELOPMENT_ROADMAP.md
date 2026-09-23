# Development Roadmap

## Current development

### 1. Substrate and reaction prediction

Delivered foundation:

- stable substrate/reaction query types;
- `substrate.to_enzyme` registry;
- local catalog provider;
- `predict_enzymes_from_substrate()`, `predict_enzymes_from_reaction()`, and `search_enzymes_by_reaction()`;
- CLI entry points;
- normalized enzyme candidate output and provenance.

Next acceptance criteria:

- chemistry-aware standardization and identifier resolution;
- at least one production reaction database provider;
- persisted reaction-similarity index;
- benchmark exact and unseen reactions;
- API exposure using the same service contract.

### 2. PLM and structure retrieval

Implementation order:

1. define `EmbeddingRecord`, cache manifest, and index manifest;
2. add a provider-neutral `EmbeddingProvider`;
3. implement one ESM-family embedding provider;
4. implement a FAISS nearest-neighbor provider;
5. implement Foldseek command execution and result normalization;
6. merge sequence, PLM, and structure hits into stable `Candidate` records.

Acceptance requires deterministic cache keys, model/index/database versions, CPU-safe unit tests, and optional GPU integration tests.

### 3. Function prediction expansion

Implementation order:

1. bind and benchmark one EC/function runner;
2. bind one catalytic-site and one substrate-compatibility runner;
3. bind kinetics, pH, stability, and solubility incrementally;
4. add enzyme/non-enzyme and family/domain/motif providers;
5. add consensus only after individual calibration is measured.

Every adapter must return `FunctionalPrediction`, preserve native artifacts, and publish availability through a health check.

### 4. Inverse folding and mutation

Implementation order:

1. add design constraints and variant lineage records;
2. implement single, multi-site, site-saturation, and selected-position mutation generation;
3. bind GeoStab/ThermoMPNN runners;
4. implement ProteinMPNN through the design registry;
5. add LigandMPNN without changing the workflow contract;
6. rank engineered candidates using the same evidence and provenance system.

### 5. Structure prediction and post-filtering

Implementation order:

1. extend typed outputs for per-residue confidence and PAE;
2. bind one deployable structure predictor;
3. create task-selective `structure_analysis` contracts;
4. add global RMSD/TM-score and Foldseek evidence;
5. add active-site and binding-site geometry;
6. add ligand, metal, clash, and interface checks only where applicable;
7. integrate validation into discovery and engineering workflows.

## Cross-cutting requirements

All work in items 1–5 must provide:

- explicit typed inputs and outputs;
- capability-scoped registration;
- stable Candidate identity and WT/variant parentage;
- `ToolResult` or an explicit mapping into it;
- software, model, database, parameter, ID, and timestamp provenance;
- CLI/API callability;
- configuration-driven provider selection;
- tests and documentation;
- no placeholder scientific predictions.

## Fixed workflows to complete

1. Known enzyme → sequence/PLM/structure retrieval → function validation → ranking.
2. Substrate/reaction → enzyme prediction → functional/structural validation → ranking.
3. Candidate enzyme → structure → inverse folding/mutation → structural validation → ranking.

## Future development: Harness / Agent

Harness and Agent work begins only after current workflows are benchmarked, reproducible, and stable. The future extension may consume the same tool APIs, but it is not part of current implementation.

Future-only scope:

- natural-language task parsing;
- LLM planning and tool routing;
- runtime state, checkpointing, scheduling, and resource management;
- critic/reflection and dynamic replanning;
- multi-agent execution;
- autonomous workflow generation.
