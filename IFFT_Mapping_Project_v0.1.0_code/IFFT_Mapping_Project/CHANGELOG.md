# Changelog

## 0.3.1 — fixed hue and zero-low preview

- All six presets use white_max=0; signed display window P0.5/P99.5 and gamma=1 remain unchanged.
- Default T_low is literal zero, T_full remains max(Gaussian(abs(F))) for this preview.
- Add reproducible six-layer/Sb-only additive black compositing with overflow and provenance records.
- Historical configs and run records retain their original settings.


## 0.3.0 — continuous alpha and separate Sb reflection previews

- Default alpha is a linear ramp from P10 to max of Gaussian(abs(real signed IFFT)); T_full remains configurable and provisional for K3SbS3.
- Save float32 opacity and alpha8; black/TEM rendering, saved-run replay and GUI use continuous opacity consistently.
- Preserve v0.2.0 D colors; add tint-to-near-white LUT and five Sb family configurations with separate batch previews.
- Keep legacy binary configurations, add legacy_v020_D.json, and retain historical filenames for compatibility.
- Update notebook, ImageJ import guidance, scientific method record and regression tests.
- No RMS, correlation, morphology, registration, or phase-boundary claim introduced.

# Change log

## 0.2.0 — 2026-10-30

- Default to D display: global signed-IFFT 0.5/99.5 percentile window and green-to-near-white LUT (start 0.55, R/B maximum 230); scalar gamma remains 1.
- Keep legacy full-range green via configs/legacy_green.json and backward-compatible function defaults.
- Share display parameters across CLI, threshold review, notebook and saved outputs.
- Record actual window, color formula and clipping fractions; retain historical output filenames for compatibility.
- Preserve original abs-Gaussian selection, Otsu threshold, binary alpha, raw inputs and TEM display handling.
- Add display/selection independence, configuration replay and headless GUI save checks; rerun the original 2048x2048 IFFT.

## 0.1.0 — 2026-10-30

- Added separate signed linear green display and abs-Gaussian detection branch.
- Sigma fixed to 5 native pixels in default config; gamma=1.
- Added editable Otsu/manual/percentile thresholds and binary-alpha extraction.
- Added transparent PNG, uncompressed TIFF, black preview and optional TEM composite.
- Added run provenance, invariant tests, interactive threshold review and ImageJ importer.
- Physical grain boundaries and phase fractions have not been validated.

