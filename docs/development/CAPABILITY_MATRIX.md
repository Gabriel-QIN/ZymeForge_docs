# Capability Matrix

Status meanings:

- **Runnable**: executes locally with repository data and no fabricated output.
- **Adapter**: normalized contract and registry metadata exist; upstream code/weights are not bound.
- **Contract**: protocol and registry exist, but no provider executes the capability.
- **Missing**: no stable implementation yet.

| Domain | Capability | Current provider/model | Status | Normalized output | Next production target |
|---|---|---|---|---|---|
| Input | reaction SMILES normalization | lexical standardizer | Runnable baseline | `NormalizedReaction` | RDKit/RDTools atom mapping, balancing, identifiers |
| Input | substrate type detection | built-in query parser | Runnable baseline | `SubstrateQuery` | resolver backed by ChEBI/PubChem/local aliases |
| Discovery | exact reaction lookup | local catalog | Runnable baseline | `SearchHit` | Rhea, KEGG, MetaCyc, BRENDA, EnzymeMap |
| Discovery | reaction similarity | character n-gram | Runnable baseline | `SearchHit` | DRFP, RXNFP, CGR, reaction-center fingerprints |
| Discovery | reaction → EC | local annotated catalog | Runnable baseline | `SearchHit` | trained ECREACT-compatible model |
| Discovery | reaction → enzyme | local reaction/protein links | Runnable baseline | `EnzymeCandidatePrediction` | CLIPZyme/Horizyn-style provider |
| Discovery | substrate → enzyme | local catalog | Runnable baseline | `EnzymeCandidatePrediction` | indexed chemical identifiers and production databases |
| Search | BLAST/MMseqs2/HMMER | none | Contract | `SearchHit` | command providers with version capture |
| Search | PLM embedding retrieval | none | Contract gap | `SearchHit` | embedding provider, cache, FAISS index |
| Search | structure similarity | none | Contract | `SearchHit` | Foldseek provider and normalized metrics |
| Function | EC/function | CLEAN, HIT-EC, EC-LMGraph | Adapter | `FunctionalPrediction` | bind and benchmark one production runner first |
| Function | catalytic site | GraphEC-AS, EC-LMGraph | Adapter | `FunctionalPrediction` | bind runner; add M-CSA template evidence |
| Function | substrate specificity | EZSpecificity, ProSmith, ESP | Adapter | `FunctionalPrediction` | bind runner and calibration dataset |
| Function | kinetics | CataPro, UniKP, TurNuP | Adapter | `FunctionalPrediction` | bind runner; normalize units and assay context |
| Function | optimum pH | EpHod, OphPred | Adapter | `FunctionalPrediction` | bind runner |
| Function | thermostability | TemBERTure, TemStaPro, DeepSTABp | Adapter | `FunctionalPrediction` | bind runner; distinguish Tm from class probability |
| Function | solubility | NetSolP | Adapter | `FunctionalPrediction` | bind runner |
| Function | cofactor | DISCODE, INSIGHT | Adapter | `FunctionalPrediction` | bind runner |
| Function | developability | SignalP, DeepTMHMM, DeepLoc | Adapter | `FunctionalPrediction` | bind licensed/available runners individually |
| Function | GO/general function | none | Missing | — | select mature provider after EC baseline |
| Function | enzyme/non-enzyme | none | Missing | — | add standardized classifier adapter |
| Function | family/domain/motif | none | Missing | — | InterProScan/HMMER/motif provider |
| Structure | monomer/complex prediction | none | Contract | `StructurePrediction` | ESMFold or another deployable first provider |
| Structure analysis | confidence and geometry QC | none | Missing | — | `StructureAnalysisResult` and task-specific checks |
| Engineering | mutation effect | GeoStab, ThermoMPNN | Adapter | `FunctionalPrediction` | bind runner and preserve WT/variant lineage |
| Engineering | mutation generation/ranking | none | Contract | `MutationCandidate` | single/multi/site-saturation generator |
| Engineering | inverse folding | none | Contract through redesign | `DesignCandidate` | ProteinMPNN first, LigandMPNN second |
| Fusion | weighted evidence ranking | weighted calibrated mean | Runnable | `ScoreCard` | learned calibration and benchmarked weights |
| Output | JSON/TSV | built-in writers | Runnable | files | report writer and artifact manifest |
| Workflow | reaction mining | fixed Python workflow | Runnable | `ReactionMiningResult` | production database providers and validation stages |
| Workflow | known-enzyme mining | none | Missing | — | sequence + PLM + structure retrieval workflow |
| Workflow | engineering | none | Missing | — | structure + inverse folding/mutation + validation |
| Runtime | Harness/Agent | none | Future only | — | excluded until platform benchmarks are complete |
