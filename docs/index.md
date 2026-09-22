# From target chemistry to ranked, engineerable enzymes

**Reaction-driven enzyme discovery**

ZymeForge unifies reaction search, sequence and structure evidence, catalytic-site geometry, functional prediction, and protein engineering behind stable Python contracts and registries.

[Install ZymeForge](getting-started/installation.md) · [Open the ZymePage Registry Catalog](zymepage.md) · [Browse registered models](registries/function-models.md)

## One framework, two directions

### Discover

Start with a reaction, substrate, product, EC number, sequence, or structure and retrieve candidate enzymes through parallel search routes.

### Rank

Fuse reaction, sequence, fold, active-site, substrate, kinetic, docking, and stability evidence into an explainable ZymeScore.

### Engineer

Send selected enzymes into mutation optimization or sequence redesign, then validate them with the same evidence stack.

```text
Target reaction
    ├── exact database lookup
    ├── reaction similarity search
    ├── reaction → EC prediction
    └── direct reaction → enzyme retrieval
                  ↓
         candidate enzyme pool
                  ↓
 sequence · structure · active site · specificity · kinetics
                  ↓
              ZymeScore
                  ↓
          mutate  ───  redesign
```

## Stable core, extensible edges

Every external database, model, or command-line tool enters through a typed adapter. The core operates on normalized records such as `ReactionRecord`, `ProteinRecord`, `EvidenceRecord`, and `ScoreCard`; upstream-specific output remains available as provenance rather than leaking into downstream workflows.

> **Honest adapter status**<br>
> A registered model is discoverable even when its checkpoint is not installed. Inference then fails explicitly with `ModelBackendUnavailable`; ZymeForge never substitutes placeholder predictions.
