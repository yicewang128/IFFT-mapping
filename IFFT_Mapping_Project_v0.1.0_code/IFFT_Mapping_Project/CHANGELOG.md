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
