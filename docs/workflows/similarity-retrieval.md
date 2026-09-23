# Protein similarity retrieval

ZymeForge exposes four complementary retrieval channels. Their native scores remain separate; the
framework does not average incomparable cosine, E-value, and TM-score values.

| Route | Representation | Required assets | Output |
|---|---|---|---|
| ESM-2 | sequence semantics | 650M checkpoint and vector index | cosine-ranked hits |
| SaProt | amino acid + 3Di | 650M checkpoint, Foldseek, vector index | structure-aware cosine hits |
| ProteinMPNN | backbone encoder | official runner/checkpoint and vector index | experimental cosine hits |
| Foldseek | 3Di + amino-acid alignment | Foldseek binary and structure database | alignment metrics |

The union is deduplicated by canonical protein ID. Optional reciprocal-rank fusion uses only ranks.
DALI then validates a configurable top-N subset and preserves Z-score, RMSD, aligned length,
sequence identity, query length, and target length as independent evidence.

## CLI

```bash
zymeforge similarity embed \
  --method esm2 --input proteins.fasta --output embeddings/esm2.jsonl

zymeforge similarity build-index \
  --method esm2 --embeddings embeddings/esm2.jsonl \
  --output indexes/esm2.npz --backend hnsw \
  --source-database UniProt --database-version 2026_03

zymeforge similarity search \
  --query query.fasta --methods esm2 \
  --index-dir indexes --top-k 100
```

Structure retrieval accepts comma-separated methods:

```bash
zymeforge similarity search \
  --query query.pdb \
  --methods saprot,proteinmpnn,foldseek \
  --index-dir indexes \
  --foldseek-db databases/foldseek/enzyme_db \
  --proteinmpnn-runner my_backend:encode_final_layer \
  --top-k 100 --dali-top-n 20 \
  --structure-map databases/candidate_structures.json
```

Every run writes `task.json`, four method-specific hit tables, `merged_hits.tsv`,
`dali_results.tsv`, `candidates.json`, `metadata.json`, and a log directory.

## API

The deployed ZymePage service accepts the same evidence model:

```http
POST /api/similarity/search
Content-Type: application/json
```

```json
{
  "query_id": "query_enzyme",
  "sequence": "MKT...",
  "methods": ["esm2"],
  "top_k": 100,
  "dali_top_n": 0,
  "use_rrf": false
}
```

The response contains `job_id`, `status`, and method-separated `results`. The service operator must
configure indexes, checkpoints, binaries, and databases. An unavailable scientific backend returns
HTTP 503 rather than placeholder hits.

## Deployment configuration

| Variable | Purpose |
|---|---|
| `ZYMEFORGE_ESM2_INDEX` | ESM-2 index bundle path |
| `ZYMEFORGE_SAPROT_INDEX` | SaProt index bundle path |
| `ZYMEFORGE_PROTEINMPNN_INDEX` | ProteinMPNN index bundle path |
| `ZYMEFORGE_PROTEINMPNN_RUNNER` | official-backend `module:function` |
| `ZYMEFORGE_FOLDSEEK_DATABASE` | Foldseek database path |
| `ZYMEFORGE_CANDIDATE_STRUCTURE_DIR` | structures used for DALI top-N validation |
| `ZYMEFORGE_SIMILARITY_DEVICE` | explicit `cuda` or `cpu` selection |

GitHub Pages hosts static documentation and the catalog interface. Scientific execution occurs on
the separately deployed ZymePage API service because GitHub Pages cannot run Python, CUDA models,
Foldseek, or DALI.
