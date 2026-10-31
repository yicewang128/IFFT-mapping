# Continue this IFFT project

Read `README.md`, then `IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/docs/CURRENT_STATE_zh.md` before changing the pipeline. The directory name is historical, not the current version.

## Scientific and data invariants

- Inputs are real signed 2D float32 IFFT images, not complex fields. Never infer raw data or thresholds from a screenshot.
- Display uses signed F with its own P0.5/P99.5 window, scalar gamma=1 and white_max=0. Keep this separate from amplitude/opacity.
- Amplitude is Gaussian(abs(F)), sigma=5 native pixels, reflect, truncate=4; NOT RMS or abs of normalized brightness.
- Confirmed K3SbS3 alpha: literal low=0, full=P80. Each of five Sb images: low=P25, full=P99.5 of its own amplitude map.
- Matrix green remains [0,255,0]. Sb colors and their names are defined in configs/sb_*.json; use configs as the single source of truth.
- Group Sb with alpha-weighted RGB and union opacity. Put that group above K3SbS3 with source-over; see src/compositing.py. Preserve the explicit legacy additive option.
- Work on original-resolution arrays. Do not add sharpening, registration, morphology, denoising, RMS/correlation or hand-drawn boundaries unless requested.
- Colors identify supplied reflection families, not individual particle identities. Display thresholds and layering do not establish physical boundaries, phase fractions or depth.

## Modify and verify

- Check the current GitHub branch head and preserve unrelated edits. Do not assume this conversation's local checkout is current.
- Read the relevant source and tests. Run `python -m pytest -q` from the project directory after changes. New compositing changes need opacity-endpoint, ordering and pixel-consistency checks.
- Run the real six-image command when inputs are available; verify source hashes, calibration, dimensions and unchanged alpha when modifying only colors.
- If experimental TIFFs are absent, say so; tests can run without them, real-image reproduction cannot. Obtain the originals through a source the user has authorized.
- Record changes in CHANGELOG.md, current-state documentation, validation/run records and the version constant. Do not rewrite historical run records.
- Never overwrite original TIFFs or existing output directories. Do not commit experimental inputs or rendered image bundles to this code repository.
- Keep machine-specific paths out of reusable code. Preserve commands that work from a fresh clone or extracted repository ZIP.
- Final reports should identify the commit, tests, real-data validation and any remaining limitations. Repository instructions should be sufficient to continue without chat history.
