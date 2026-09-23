# CLI reference

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
