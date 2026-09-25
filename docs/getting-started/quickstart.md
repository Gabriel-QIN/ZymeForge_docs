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

## Search a configured sequence database

List configured resources and run MMseqs2 against the one-million-sequence example:

```bash
zymeforge database list
zymeforge similarity alignment-search \
  --method mmseqs2 \
  --query query.fasta \
  --database uniref90_example_1m_mmseqs \
  --output runs/mmseqs_hits.tsv
```

Use a complete database by name, such as `uniref90` or `nr`, or pass an explicit path:

```bash
zymeforge similarity alignment-search \
  --method mmseqs2 \
  --query query.fasta \
  --database /data/custom/proteins.fasta \
  --output runs/custom_hits.tsv
```

## Validate a workflow

```bash
zymeforge validate-workflow configs/reaction_to_enzyme.yaml
```
