# Gap Analysis

## Audit conclusion

The repository has a coherent registry kernel, stable reaction-domain records, a runnable local reaction-mining baseline, evidence fusion, output writers, and broad function-model metadata. The main gap is not package organization; it is production provider depth. Most high-value scientific capabilities are contracts or adapters without executable upstream implementations.

## Highest-priority gaps

### 1. Production substrate/reaction discovery

The new discovery facade and local catalog provider establish the public API and normalized output, but the demo catalog is small. InChI, InChIKey, and substrate-name support depends on catalog metadata and does not yet call an external resolver.

Required next work:

1. chemistry-aware molecule/reaction normalization;
2. versioned Rhea/KEGG/MetaCyc/EnzymeMap ingestion providers;
3. reaction fingerprints and a persisted similarity index;
4. production reaction-to-EC and direct reaction-to-enzyme providers;
5. benchmark sets for exact, orphan, and non-natural reactions.

### 2. Sequence, PLM, and structure retrieval

Sequence and structure protocols exist, but no BLAST, MMseqs2, HMMER, PLM, or Foldseek provider is runnable. There is no embedding record, cache key, or index manifest.

The next contract must include model name/version, sequence hash, embedding dimension, pooling strategy, index version, database version, and provenance. Cache invalidation must be based on all of these fields, not only sequence ID.

### 3. Function prediction depth

The adapter catalog is broad but not operational without runners. General GO prediction, enzyme/non-enzyme classification, family/domain annotation, and motif detection are absent. Existing output values are flexible dictionaries; production integration needs task-specific value schemas and units where appropriate.

Integration should begin with one model per high-value dimension, validate its license and checkpoint availability, and add a benchmark before enabling consensus.

### 4. Engineering implementation

Mutation and redesign interfaces exist, but only mutation model cards are registered. There is no mutation generator, site-saturation implementation, inverse-folding provider, or full WT → variant lineage workflow. `Candidate.parent_candidate_id` now provides the shared lineage anchor.

### 5. Structure prediction and analysis

`StructurePrediction` covers a structure path, pLDDT, pTM, ipTM, and metadata, but lacks per-residue confidence and PAE artifacts as typed fields. No predictor is bound. No structure-analysis package exists for RMSD, TM-score, active-site geometry, ligand distances, clashes, metal coordination, interfaces, or buried surface area.

Structure analysis must be task-selective; enzyme mining must not be forced to compute binder-only interface metrics.

### 6. Candidate and result migration

`Candidate`, `ToolResult`, and `ProvenanceRecord` now define the target contracts. Existing `ReactionMiningResult`, `FunctionalPrediction`, `StructurePrediction`, `MutationCandidate`, and `DesignCandidate` should be wrapped or mapped incrementally. A flag-day rewrite would add risk without improving scientific capability.

## Technical debt and risks

| Risk | Evidence | Mitigation |
|---|---|---|
| Registration may be mistaken for model availability | function adapters exist without runners | preserve explicit health checks and backend-unavailable errors |
| Reaction similarity can overstate chemistry | current n-gram baseline is lexical | label it baseline; replace with chemistry-aware representations |
| Database versions can be lost | local catalog version is currently composition-time metadata | add catalog manifests and checksums |
| Score calibration is not benchmarked | fixed weights in `WeightedEvidenceFusion` | publish benchmark splits and calibration metrics |
| IDs can diverge across tools | legacy results use several record types | use protein ID plus stable `candidate:<protein_id>` identity |
| GPU environment and CI differ | CI intentionally installs core only | keep contract tests CPU-safe; add separate CUDA integration workflow later |
| External licenses vary | SignalP and some upstream tools have restrictions | record license in every plugin and gate distributable images |

## Explicit non-goals

No current gap should be solved by introducing an LLM planner, Agent loop, critic, reflection, dynamic replanning, multi-agent system, natural-language router, or Harness runtime. These do not replace missing scientific providers or benchmarks.
