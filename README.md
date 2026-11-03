# IFFT-mapping

Academic research-library tools plus reproducible signed-IFFT lattice display for TEM figures.

**Research library v1.1.0:** local papers, textbooks, page-numbered full-text search, source-linked reading and writing-analysis cards, and research project templates. Start with the [academic workflow and Windows upgrade guide](docs/ACADEMIC_RESEARCH_WORKFLOW_zh.md). It is a local foundation, not an automatic AI reader, remote connection or complete graphical platform.

**IFFT pipeline version: v0.4.1.** Start with [current workflow, parameters and continuation guide](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/docs/CURRENT_STATE_zh.md).
Coding agents should read [AGENTS.md](AGENTS.md) first. These files describe the project without needing the original chat.

- K3SbS3: green [0,255,0], alpha from literal0 to P80 of Gaussian(abs(F)).
- Each Sb family: its own P25 to P99.5; distinct royal blue, coral red, violet, bright yellow and bright orange colors.
- Signed display P0.5/P99.5, gamma1, white_max0; Gaussian sigma5 native pixels only in the amplitude branch.
- Default composite: group the five Sb layers with weighted color/union opacity, then place Sb above the matrix using source-over. Explicit legacy additive mode remains available.

[Installation and commands](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/README.md) · [Methods](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/docs/METHODS_zh.md) · [Change log](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/CHANGELOG.md)

The historical project directory name is retained to preserve paths. Experimental TIFFs and generated results are not stored in this code repository. A repository link provides code and processing context; reproducing experimental figures also requires the six original IFFTs and permission to access them. See the input layout in data/README.md.

## Local research library (separate tool v1.1.0)

Read the [Windows setup and classification guide](docs/LOCAL_RESEARCH_LIBRARY_zh.md).
Download/extract the repository and open `START_RESEARCH_LIBRARY_WINDOWS.cmd`,
then enter your existing local library folder. The tool checks access, creates
folders, indexes file hashes, and copies Inbox files into provisional categories.
It preserves originals, avoids overwrites, and does not upload files or establish
remote access. The user's actual PC access must be verified on that PC.
The IFFT pipeline remains v0.4.1 with unchanged scientific processing.

For PDF reading/indexing install `python -m pip install -r tools/requirements-library.txt`.
The Windows menu now includes full-text indexing (7), page-linked search (8),
reading/writing-analysis cards (9), research projects (10), and reading a source page (11).
All document content, extracted text and notes stay local; no network requests are made by these tools.
