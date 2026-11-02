# IFFT-mapping

Reproducible signed-IFFT lattice display and amplitude-based opacity for TEM figures.

**Current version: v0.4.1.** Start with [current workflow, parameters and continuation guide](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/docs/CURRENT_STATE_zh.md).
Coding agents should read [AGENTS.md](AGENTS.md) first. These files describe the project without needing the original chat.

- K3SbS3: green [0,255,0], alpha from literal0 to P80 of Gaussian(abs(F)).
- Each Sb family: its own P25 to P99.5; distinct royal blue, coral red, violet, bright yellow and bright orange colors.
- Signed display P0.5/P99.5, gamma1, white_max0; Gaussian sigma5 native pixels only in the amplitude branch.
- Default composite: group the five Sb layers with weighted color/union opacity, then place Sb above the matrix using source-over. Explicit legacy additive mode remains available.

[Installation and commands](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/README.md) · [Methods](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/docs/METHODS_zh.md) · [Change log](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/CHANGELOG.md)

The historical project directory name is retained to preserve paths. Experimental TIFFs and generated results are not stored in this code repository. A repository link provides code and processing context; reproducing experimental figures also requires the six original IFFTs and permission to access them. See the input layout in data/README.md.

