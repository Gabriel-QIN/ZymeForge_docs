# CLI reference

## Engineering

```bash
zymeforge engineer redesign --help
zymeforge engineer score --help
zymeforge engineer mutate --help
```

The redesign and score commands wrap the unmodified official LigandMPNN scripts. Mutation
prediction wraps the official unZipro mutation script. Provider-specific arguments are supplied
through a validated JSON `--options` file; generated JSON retains the full parameters and
provenance.

## Structure

```bash
zymeforge structure predict --help
zymeforge structure compare --help
zymeforge structure active-site --help
zymeforge structure ligand --help
zymeforge structure quality --help
```

Prediction commands call explicitly configured official providers. Comparison, geometry, and QC
commands preserve native metrics and never apply acceptance thresholds automatically.

| Command | Description |
|---|---|
| `zymeforge run-reaction` | run the local reaction-mining workflow |
| `zymeforge validate-workflow` | validate workflow YAML and dependencies |
| `zymeforge registries` | list typed extension points |
| `zymeforge plugins` | list configured providers |
| `zymeforge models` | list functional and mutation adapters |
| `zymeforge similarity embed` | batch ESM-2, SaProt, or ProteinMPNN embeddings |
| `zymeforge similarity build-index` | build Flat/HNSW index plus provenance manifest |
| `zymeforge similarity build-structure-db` | build a Foldseek database |
| `zymeforge similarity search` | run independent retrieval routes and optional DALI |
| `zymepage web` | serve the separate ZymePage catalog and model API |

Use `--help` at any level for current options:

```bash
zymeforge --help
zymeforge run-reaction --help
zymeforge similarity --help
zymepage web --help
```
