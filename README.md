# IFFT Mapping — v0.2.0

K₃SbS₃ signed-IFFT color display with a separate abs → Gaussian → threshold selection.

项目代码位于 [IFFT_Mapping_Project](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project)。
目录保留首次上传时的名字，当前程序版本为v0.2.0。

- [安装、运行及D/A切换](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/README.md)
- [处理步骤与理由](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/docs/METHODS_zh.md)
- [原始IFFT复跑验证](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/docs/RUN_002_zh.md)
- [默认D参数](IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project/configs/default.json)

在项目目录运行 `python src/review_mask.py`，选择原始IFFT。
默认D使用收窄显示窗口和近白色高亮，原版A可用 `--config configs/legacy_green.json`。
实验原图和生成结果不包含在此代码仓库；区域mask属于探索性信号选择，不是已验证的物理晶界。
