# Operations and benchmarks

## Tool availability

Inspect the unified environment before launching an expensive workflow:

```bash
zymeforge harness health
zymeforge harness health --json
```

The deployed API exposes the same report at `GET /api/health/tools`. Each tool lists its
binary, checkpoint/index/database path, license gate, and execution-handler status. A failed
component makes the tool unavailable; it does not create a synthetic result.

## Shared database catalog

The local catalog uses `/mnt/data2/database` as a stable indirection layer. Source datasets
remain under `/mnt/data/AI4Protein/database`; symbolic links prevent multi-hundred-gigabyte
copies while keeping project configuration stable.

| Name | Type | Local state |
|---|---|---|
| `afesm`, `eemc`, `gopc`, `logan`, `nr`, `uniref90` | protein FASTA | linked and resolvable |
| `uniref90_example_1m` | protein FASTA | 1,000,000 records, deterministic prefix sample |
| `uniref90_example_1m_mmseqs` | MMseqs2 DB | materialized and indexed |
| `afdb` | Foldseek archive | linked; extraction still required |

The one-million-record example contains 2,875,757,154 residues and occupies about 2.9G as
FASTA. Its persistent MMseqs2 index avoids rebuilding the k-mer table on every query.

## Benchmark definitions

The core repository includes versioned manifests for:

- CATH/SCOPe retrieval, including `<30%` and `<20%` sequence-identity subsets;
- exact, unseen and orphan reaction retrieval;
- evidence calibration and candidate ranking with grouped holdouts.

Manifests remain in `definition` state until datasets are version-pinned and real result
files exist. ZymeForge therefore distinguishes benchmark design from measured performance.

## Run provenance

Harness tool results record start and finish timestamps, elapsed seconds, parameters,
tool version, Python/runtime information, provider provenance, normalized outputs and
artifacts. The run store writes these into the run directory together with candidates and
an HTML report.
