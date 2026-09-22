# Quickstart

<!-- Core ZymeForge CLI examples -->

## Run reaction-to-enzyme mining

```bash
zymeforge run-reaction \
  --reaction "CCO.O>>CC=O.O" \
  --ph 7.0 \
  --temperature-c 30 \
  --top-k 10
```

Write complete candidates, evidence records, and score cards to JSON:

```bash
zymeforge run-reaction \
  --reaction "CCO.O>>CC=O.O" \
  --json \
  --output runs/ethanol-oxidation.json
```

## Inspect capabilities

```bash
zymeforge registries
zymeforge plugins
zymeforge models
```

`registries` lists supported extension points, `plugins` lists configured providers, and `models` lists Functional Prediction Registry adapters.

## Validate a workflow

```bash
zymeforge validate-workflow configs/reaction_to_enzyme.yaml
```
