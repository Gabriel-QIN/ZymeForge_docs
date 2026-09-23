# Structure prediction and post-screening

ZymeForge separates prediction confidence, global fold similarity, local catalytic geometry,
ligand-pocket geometry, and stereochemical quality. Native scores are retained as independent
evidence rather than averaged into an undocumented structure score.

```text
sequence
  ↓
ESMFold screening / Boltz-2 / local AlphaFold 3
  ↓
model confidence and per-residue confidence
  ↓
Foldseek → US-align/TM-align → DALI
  ↓
active-site geometry → ligand/metal geometry → MolProbity QC
  ↓
nullable StructureScreeningRecord → candidate ranking
```

## Prediction providers

| Provider | Intended use | Inputs | Preserved outputs |
| --- | --- | --- | --- |
| ESMFold | high-throughput single-chain screening | sequence | structure, mean/per-residue pLDDT, pTM |
| Boltz-2 | detailed protein, complex, and ligand prediction | chains, ligand, cofactors | confidence, complex confidence, pTM, ipTM, affinity output |
| AlphaFold 3 | detailed local prediction when legally configured | proteins, ligand, nucleic acid | structure, PAE, pTM, ipTM, ranking confidence |

AlphaFold 3 remains unavailable until the deployment operator supplies an official source tree,
model parameters, and databases. ZymeForge neither downloads nor bypasses the parameter terms.

ESMFold requires a local official checkpoint and its official OpenFold runtime dependency. The
wrapper never silently downloads weights during an API request.

## Confidence layers

`StructureResult` retains nullable model-native metrics:

```text
mean pLDDT
per-residue pLDDT
PAE matrix and artifact
pTM / ipTM
model confidence / complex confidence
affinity output
active-site pLDDT / pocket pLDDT
runtime, artifacts, parameters, provenance
```

Active-site and pocket confidence are computed from the preserved per-residue values only after
the caller supplies positions. They are not inferred from the global mean.

## Global comparison

- Foldseek retains E-value, identity, coverage, alignment TM-score, query/target TM-score, and
  lDDT.
- US-align/TM-align retains both length-normalized TM-scores, RMSD, aligned length, and sequence
  identity.
- DALI retains Z-score, RMSD, aligned length, sequence identity, and structure lengths as an
  independent evidence source.

No homology or acceptance threshold is hard-coded. Benchmarks determine downstream thresholds.

## Active-site validation

```python
from zymeforge.structure.active_site import compare_active_site

result = compare_active_site(
    "candidate.pdb",
    "reference.pdb",
    ("A:42", "A:105", "A:178"),
    pocket_residues=("A:40", "A:41", "A:43", "A:104", "A:106"),
)
```

The local superposition reports catalytic-atom RMSD, residue-center distances and angles, pocket
RMSD, residue conservation, local pLDDT, and deltas from the reference geometry. This evidence is
kept separate from global TM-score.

## Ligand and metal analysis

The ligand layer reports minimum protein distance, contacts, clashes, distance-defined hydrogen
bonds, contact residues, ligand RMSD, metal-residue distances, coordination number, and candidate
coordination geometry. Metal coordination bonds are not misclassified as steric clashes.

Pocket volume and buried surface area remain null unless supplied by a configured mature external
provider. Salt bridges remain null unless formal charges are assigned; atom identity alone is not
used to fabricate charge evidence.

## Structure quality

The MolProbity provider calls the mature external implementation and parses clash score,
Ramachandran outliers, bond/angle outliers, missing residues, and chain breaks. Missing executable
or unrecognized output causes an explicit failure.

## Mutant post-screening

WT and mutant structures are compared with the same evidence types:

```text
global RMSD and TM-score
active-site RMSD and pocket RMSD
ΔpLDDT and ΔpTM
clash-score change
ligand-geometry changes
```

ZymeForge does not equate a high mutant pLDDT with improved enzyme function. Fold preservation,
catalytic geometry preservation, and functional-property evidence remain separate decisions.

## CLI

```bash
zymeforge structure predict --method esmfold --sequence ACDE... \
  --esmfold-checkpoint models/esmfold_3B_v1.pt

zymeforge structure compare --query mutant.pdb --target wt.pdb --binary TMalign

zymeforge structure active-site --query mutant.pdb --reference wt.pdb \
  --catalytic-residues A:42,A:105,A:178

zymeforge structure ligand --structure complex.pdb --ligand-id LIG
zymeforge structure quality --structure model.pdb
```

## API and deployment

```text
POST /api/structures/predict
POST /api/structures/compare
POST /api/structures/active-site
POST /api/structures/ligand
POST /api/structures/quality
```

Prediction paths, checkpoints, databases, and binary locations are server-managed. Required
variables depend on the enabled providers:

```text
ZYMEFORGE_BOLTZ_BINARY
ZYMEFORGE_ESMFOLD_CHECKPOINT
ZYMEFORGE_AF3_SOURCE
ZYMEFORGE_AF3_MODEL_DIR
ZYMEFORGE_AF3_DATABASE_DIR
ZYMEFORGE_USALIGN_BINARY
ZYMEFORGE_MOLPROBITY_BINARY
```

API clients submit sequences or structure text, never arbitrary server filesystem paths.
