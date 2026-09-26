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
| `zymeforge database list` | list named sequence and structure databases |
| `zymeforge database resolve` | resolve a database name or explicit path |
| `zymeforge database sample-fasta` | create a deterministic first-N FASTA example and manifest |
| `zymeforge database ensure` | report readiness for every configured database |
| `zymeforge database download` | resumably download a configured sequence database from an official source |
| `zymeforge database foldseek-download` | invoke the official `foldseek databases` downloader |
| `zymeforge model-hub list` | list model assets, compatibility state, and local paths |
| `zymeforge model-hub download` | download selected public assets from official Hugging Face repositories |
| `zymeforge model-hub verify` | verify downloaded asset directories |
| `zymeforge model-hub status` | distinguish downloaded assets from runnable providers |
| `zymeforge similarity embed` | batch ESM-2, SaProt, or ProteinMPNN embeddings |
| `zymeforge similarity build-index` | build Flat/HNSW index plus provenance manifest |
| `zymeforge similarity build-structure-db` | build a Foldseek database |
| `zymeforge similarity search` | run independent retrieval routes and optional DALI |
| `zymeforge similarity alignment-search` | run MMseqs2, phmmer, or HHsearch |
| `zymeforge harness health` | inspect tools, assets, databases, licenses, and handlers |
| `zymeforge agent tools` | list tools the natural-language Planner may call |
| `zymeforge agent plan/run` | compile natural language and execute the validated Harness plan |
| `zymeforge harness compose` | create or execute the same plan contract without an LLM |
| `zymepage web` | serve the separate ZymePage catalog and model API |

Use `--help` at any level for current options:

```bash
zymeforge --help
zymeforge run-reaction --help
zymeforge similarity --help
zymeforge database --help
zymepage web --help
```
