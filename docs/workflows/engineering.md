# Engineering

<!-- Mutation and redesign workflows -->

Candidate selection branches into two parallel engineering strategies.

## Mutation engineering

Mutation engineering preserves most of an existing enzyme and evaluates targeted substitutions. Registry V1 includes GeoStab and ThermoMPNN adapters for mutation effects. A mutation workflow can combine stability, activity, fitness, structural confidence, and catalytic geometry.

```text
selected enzyme → mutation proposals → effect prediction → multi-objective rank → validation
```

## Sequence redesign

Redesign can replace a local region, rebuild a pocket, or generate a new sequence under structural and functional constraints.

```text
selected scaffold + constraints → redesign → structure/function consistency → validation
```

Both paths return normalized evidence and can therefore reuse ZymeScore calibration and reporting instead of creating a separate ranking system.
