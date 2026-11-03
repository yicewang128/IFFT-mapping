# Changelog

## 2026-11-03 — separate local research-library tool v1.0.0

- Add a root-scoped local utility, Windows menu, provisional Inbox classification by verified byte-preserving copies, SHA256 catalogs and filename/text lookup.
- Add filesystem tests and Ubuntu/Windows CI for the independent utility.
- Record that the cloud session has no connection to the user's Windows C: drive; local checks are required.
- IFFT pipeline version remains 0.4.1. No display, amplitude, alpha, color or compositing changes.

## 0.4.1 — confirmed bright-orange Sb {024}

- Change only Sb {024} base RGB from [255,65,170] to [255,128,0], with color_name bright orange.
- Preserve every other color, signed display, alpha threshold and layered compositing rule.
- Rerun all six original IFFTs and deliver eight native-resolution uncompressed RGB8 TIFFs on black: six individuals, grouped Sb, and Sb above the matrix.
- Record original hashes, calibration, pixel comparisons and the rerun in RUN_007_zh.md.

## 0.4.0 — distinct Sb colors and reproducible layered composition

- Keep matrix green; update Sb to royal blue, coral red, violet, bright yellow and rose pink. Configs hold both RGB and color names.
- Preserve the confirmed K3 0/P80 and per-family Sb P25/P99.5 opacity endpoints, signed display and sigma5 amplitude processing.
- Add order-independent weighted-color/union-opacity Sb grouping and source-over above the matrix as the default combined mode. Preserve explicit --compositing additive.
- Export combined transparent layers as well as black PNG/TIFF, and record composition rules and module hashes.
- Add repository AGENTS.md and a current-state handoff guide, input layout, and compositing regression tests.

## 0.3.2 — confirmed per-material alpha endpoints

- K3SbS3 default: literal T_low=0, T_full=P80 of Gaussian(abs(F)).
- Five Sb presets: T_low=P25 and T_full=P99.5, computed independently on each image.
- Preserve fixed hues (white_max=0), signed display P0.5/P99.5, gamma=1, sigma=5px, legacy presets and existing compositing behavior.
- Update the notebook and method/usage documentation to distinguish display percentiles from opacity percentiles.
- Remove obsolete max labels from Sb previews; rename the batch CSV column T_full_max to T_full because it stores the resolved endpoint under any mode.

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


