# RT and PET hydrolase validation

The sequence, structure, and reaction-driven mining routes were validated with positive controls on 26 September 2026.

| Workflow | Positive-control result | Status |
|---|---|---|
| Reverse transcriptase sequence search | RNA-directed DNA polymerase `UniRef90_A0A0N5BI89`, rank 4, E-value `4.049e-18` | Passed |
| Reverse transcriptase structure search | SIV Gag-Pol/RT `P27973`, rank 2, E-value `4.427e-49` | Passed |
| PET hydrolase reaction/EC search | LCC `G9BY57` rank 1; IsPETase `A0A0K8P6T7` rank 4 | Passed for reference recovery |
| PET hydrolase sequence expansion | Only a weak, annotation-inconsistent target | No novel candidate validated |

## Resources

The RT sequence query was searched with MMseqs2 against the one-million-entry UniRef90 example database. Targets were limited to 2,000 residues. The structure query was the public experimental PDB 1RTD and was searched with Foldseek against 351,242 structures from the locally indexed BFVD archive.

The BFVD index is configured as `databases.structure.bfvd`; its local files are not distributed with ZymeForge. Structure-aware embedding retrieval for a project-specific target remains pending an appropriate query PDB.

## PET screening conditions

The reaction test uses BHET mono-hydrolysis as a PET-hydrolysis surrogate and EC `3.1.1.101`, at 50 °C and pH 8.0. Candidate screening is configured with:

- length 180–800 aa, no transmembrane helix, and reaction/EC consistency;
- a `G-x-S-x-G` nucleophile motif and a Ser–Asp/Glu–His catalytic triad;
- active-site pLDDT ≥ 70 when a structure is available;
- nucleophile-to-carbonyl and catalytic-relay distances ≤ 3.5 Å;
- nucleophilic attack angle 85–115° and no severe ligand clash;
- substrate compatibility, kinetics, pH, thermostability, solubility, developability, and sequence diversity as ranking evidence.

An unavailable predictor contributes missing evidence, never a generated placeholder score. The PET sequence-expansion result therefore does **not** support a new PETase claim; the successful result is recovery of known reaction- and EC-linked enzymes.
