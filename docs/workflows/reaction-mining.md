# Reaction-to-enzyme mining

<!-- Reaction-driven discovery workflow -->

Reaction mining begins with chemistry rather than a known protein query.

## Input

The primary input is a reaction SMILES string:

```text
substrate_1.substrate_2>>product_1.product_2
```

`ReactionContext` can attach pH, temperature, organism, compartment, and cofactors without changing reaction identity.

## Parallel retrieval routes

1. **Exact lookup** — match standardized chemistry to reaction databases and retrieve linked EC, KO, and protein identifiers.
2. **Similarity search** — compare reaction fingerprints or embeddings to known reactions.
3. **Reaction-to-EC** — infer enzyme classes, then retrieve matching sequences.
4. **Direct reaction-to-enzyme** — rank proteins in a shared reaction/protein representation space.

Candidates are merged by stable protein identity while retaining every retrieval route.

## Refinement

The merged pool can be refined using substrate compatibility, functional consensus, catalytic-site geometry, structure prediction, docking constraints, kinetics, stability, and developability. These signals enter evidence fusion and produce a ranked candidate list for experimental selection.

## Configuration

```bash
zymeforge validate-workflow configs/reaction_to_enzyme.yaml
```

The YAML definition captures step dependencies; runtime provider selection remains in the corresponding registry.
