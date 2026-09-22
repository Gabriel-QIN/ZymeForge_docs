# Evidence fusion

<!-- Multi-source ranking concepts -->

No single signal is sufficient for enzyme discovery. ZymeForge represents each signal as an `EvidenceRecord`, preserving its source, native score, normalized score, confidence, and provenance.

## ZymeScore

The ranking interface combines complementary dimensions:

\[
S_{Zyme} = f(S_{reaction}, S_{sequence}, S_{structure}, S_{active-site},
S_{substrate}, S_{function}, S_{kinetics}, S_{docking}, S_{stability})
\]

The baseline `WeightedEvidenceFusion` computes a calibrated weighted mean over available evidence. Missing dimensions are reported rather than silently treated as zero.

## Score card

A `ScoreCard` contains:

- final `zyme_score` and confidence;
- per-dimension contributions;
- available and missing evidence dimensions;
- source routes and warnings;
- provenance required to reproduce the rank.

This allows a scientist to distinguish a high score supported by multiple independent routes from a similar score driven by one uncertain predictor.
