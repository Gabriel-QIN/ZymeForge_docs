<!-- ZymeForge documentation home -->
<div class="hero" markdown>
<span class="zf-kicker">Reaction-driven enzyme discovery</span>

# From target chemistry to ranked, engineerable enzymes.

ZymeForge unifies reaction search, sequence and structure evidence, catalytic-site geometry, functional prediction, and protein engineering behind stable Python contracts and registries.

[Install ZymeForge](getting-started/installation.md){ .md-button .md-button--primary }
[Browse registered models](registries/function-models.md){ .md-button }
</div>

## One framework, two directions

<div class="zf-grid">
  <div class="zf-card"><strong>Discover</strong><p>Start with a reaction, substrate, product, EC number, sequence, or structure and retrieve candidate enzymes through parallel search routes.</p></div>
  <div class="zf-card"><strong>Rank</strong><p>Fuse reaction, sequence, fold, active-site, substrate, kinetic, docking, and stability evidence into an explainable ZymeScore.</p></div>
  <div class="zf-card"><strong>Engineer</strong><p>Send selected enzymes into mutation optimization or sequence redesign, then validate them with the same evidence stack.</p></div>
</div>

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

!!! info "Honest adapter status"
    A registered model is discoverable even when its checkpoint is not installed. Inference then fails explicitly with `ModelBackendUnavailable`; ZymeForge never substitutes placeholder predictions.
