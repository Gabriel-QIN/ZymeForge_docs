# Python contracts

<!-- Stable ZymeForge domain records -->

## Core records

| Contract | Purpose |
|---|---|
| `ReactionRecord` | normalized chemistry and identifiers |
| `ProteinRecord` | stable protein identity and sequence metadata |
| `CandidateReactionPair` | reaction/protein association and retrieval routes |
| `EvidenceRecord` | one scored observation with provenance |
| `ScoreCard` | fused score, confidence, contributions, and warnings |
| `FunctionalPrediction` | normalized output from function model adapters |
| `SimilarityHit` | one method-specific sequence or structure retrieval hit |
| `EmbeddingRecord` | representation plus hashes, checkpoint, pooling, and provenance |
| `IndexManifest` | database, model, metric, backend, counts, version, and timestamp |
| `MergedSimilarityCandidate` | canonical target with independent per-method hits |
| `DaliResult` | top-N structural validation evidence |

`SimilarityHit.method` includes `tmvec`, `dhr`, and `protrek`. ProTrek hits preserve query and
target modality; DHR hits preserve the asymmetric query/target encoder identity.

Pydantic validates data at adapter boundaries. Serialization uses JSON-compatible values so records can be written by output plugins or transported through the web API.

```python
from zymeforge.core.models import ReactionContext

context = ReactionContext(ph=7.0, temperature_c=30.0)
```

Contracts are intentionally smaller than upstream tool output. Preserve additional tool-specific content as provenance artifacts instead of expanding shared records for one provider.
