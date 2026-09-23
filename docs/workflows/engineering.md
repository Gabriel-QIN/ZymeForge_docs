# Redesign and mutation prediction

ZymeForge exposes two parallel engineering branches after enzyme mining. They share the
existing Candidate and Registry contracts, but they do not represent the same scientific task.

```text
selected enzyme
├── structure-conditioned sequence redesign → LigandMPNN
└── function-oriented mutation prediction  → unZipro
```

No model architecture is copied into ZymeForge. Both providers call their official upstream
inference scripts and preserve flags, checkpoints, seeds, runtime, artifacts, and source revision
in run metadata. Missing source trees or checkpoints produce an explicit error.

## LigandMPNN redesign

The `design_model` registry contains one LigandMPNN provider with five model modes:

- `protein_mpnn`
- `ligand_mpnn`
- `soluble_mpnn`
- `global_label_membrane_mpnn`
- `per_residue_label_membrane_mpnn`

The same wrapper supports global redesign, local pocket redesign, membrane labels, symmetry,
amino-acid bias/omission constraints, ligand atom and fixed-side-chain context, and official
side-chain packing. `fixed_residues` protects catalytic or coordinating residues;
`redesigned_residues` limits sampling to a selected shell.

```python
from pathlib import Path

from zymeforge.engineer.redesign import LigandMPNNProvider

provider = LigandMPNNProvider("/opt/LigandMPNN")
designs = provider.design_sequence(
    "enzyme_with_ligand.pdb",
    model_type="ligand_mpnn",
    options={
        "out_folder": Path("runs/pocket-redesign"),
        "checkpoint_ligand_mpnn": Path("models/ligandmpnn.pt"),
        "fixed_residues": "A42 A105 A178",
        "redesigned_residues": "A40 A41 A43 A104 A106",
        "temperature": 0.1,
        "seed": 17,
        "batch_size": 10,
        "number_of_batches": 10,
        "ligand_mpnn_use_atom_context": True,
    },
)
```

The normalized result includes the designed sequence, chain-aware mutation list, confidence,
model type, checkpoint, full parameters, input/output structures, artifacts, runtime, source
commit, and checkpoint SHA-256.

## LigandMPNN scoring

Official `score.py` is available through four normalized modes:

| Mode | Sequence context | Official scoring path |
| --- | --- | --- |
| `single_aa` | enabled | single-AA |
| `autoregressive` | enabled | autoregressive |
| `sequence_conditioned` | enabled | single-AA conditioned |
| `backbone_only` | disabled | single-AA backbone-only |

`score.py` reads residue identities from the submitted PDB. To compare WT, mutant, and design,
submit a matching structure for each sequence; the optional sequence field is provenance, not a
replacement for the PDB sequence.

## unZipro mutation prediction

unZipro is registered under `mutation_predictor`, not as inverse folding. The current official
inference script is structure-aware and emits ranked single substitutions. Therefore the wrapper
requires both the parent sequence and a PDB; it does not claim sequence-only or native
multi-mutation support.

The parser preserves `mut_prob`, `model_prob`, WT probability, logits, logit ratio, author residue
number, and chain. A mutant sequence is generated only when an explicit `chain:author_position`
to sequence-position mapping is provided. This prevents silent errors from insertion codes or
non-contiguous PDB numbering.

## CLI

All commands consume a JSON options object so the official parameter surface remains available:

```bash
zymeforge engineer redesign \
  --source-dir /opt/LigandMPNN \
  --structure enzyme.pdb \
  --options redesign.json \
  --output designs.json

zymeforge engineer score \
  --source-dir /opt/LigandMPNN \
  --structure mutant.pdb \
  --options score.json \
  --output scores.json

zymeforge engineer mutate \
  --source-dir /opt/unZipro \
  --structure enzyme.pdb \
  --sequence ACDE... \
  --parent-id enzyme-1 \
  --options unzipro.json \
  --top-k 100 \
  --output mutations.json
```

## ZymePage API

The deployed service exposes:

```text
POST /api/engineering/redesign
POST /api/engineering/score
POST /api/engineering/mutations
```

The service stages submitted PDB text in an isolated temporary run directory. Source trees,
checkpoints, configs, output folders, and other filesystem paths are server-managed and cannot be
supplied by API clients.

Required deployment variables:

```text
ZYMEFORGE_LIGANDMPNN_SOURCE
ZYMEFORGE_PROTEIN_MPNN_CHECKPOINT
ZYMEFORGE_LIGAND_MPNN_CHECKPOINT
ZYMEFORGE_SOLUBLE_MPNN_CHECKPOINT
ZYMEFORGE_GLOBAL_MEMBRANE_MPNN_CHECKPOINT
ZYMEFORGE_PER_RESIDUE_MEMBRANE_MPNN_CHECKPOINT
ZYMEFORGE_LIGANDMPNN_SIDECHAIN_CHECKPOINT

ZYMEFORGE_UNZIPRO_SOURCE
ZYMEFORGE_UNZIPRO_CHECKPOINT
ZYMEFORGE_UNZIPRO_CONFIG
ZYMEFORGE_ENGINEERING_GPU
```

An endpoint returns HTTP 503 when its official backend or checkpoint is not configured. It never
returns placeholder scientific predictions.
