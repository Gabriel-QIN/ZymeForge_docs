# Functional Prediction Registry V1

<!-- Registry catalog -->

All adapters use the shared `UnifiedFunctionModel` runtime and return `FunctionalPrediction` records.

| Dimension | Registered models | Normalized output |
|---|---|---|
| EC / function | CLEAN, HIT-EC, EC-LMGraph | EC number and confidence |
| Catalytic site | GraphEC-AS, EC-LMGraph | residues and local confidence |
| Substrate specificity | EZSpecificity, ProSmith, ESP | compatibility probability |
| Kinetics | CataPro, UniKP, TurNuP | kcat, Km, kcat/Km |
| Optimal pH | EpHod, OphPred | pH optimum |
| Thermostability | TemBERTure, TemStaPro, DeepSTABp | Tm or stability probability |
| Solubility | NetSolP | soluble probability |
| Cofactor specificity | DISCODE, INSIGHT | cofactor preference |
| Developability | SignalP, DeepTMHMM, DeepLoc | signal peptide, TM, localization |
| Mutation effects | GeoStab, ThermoMPNN | ΔΔG, ΔTm, fitness |

Inspect the installed catalog:

```bash
zymeforge models
```

Registration makes metadata discoverable. A model becomes runnable when its upstream implementation and checkpoint are bound through a runner in the unified environment.
