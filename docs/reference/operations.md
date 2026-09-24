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
