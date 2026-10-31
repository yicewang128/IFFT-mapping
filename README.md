# IFFT-mapping

Reproducible signed-IFFT color display and local amplitude opacity for TEM figures.

Current version: **v0.3.2**. Continuous alpha replaces default Otsu binary alpha.
All six presets use fixed hue (white_max=0). Confirmed endpoints on Gaussian(abs(F)):
K3SbS3 uses literal T_low=0 and T_full=P80 (top 20% fully opaque); each Sb family independently uses T_low=P25 and T_full=P99.5 (top 0.5% fully opaque).
A six-layer additive black compositor is included; this parameter update does not change its blending rule.

Open [the project and instructions](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/README.md).
The older directory name is retained to preserve existing paths.

The project includes five independently colored Sb reflection-family presets and a batch runner.
Experimental TIFFs and generated results are kept outside this code repository.

