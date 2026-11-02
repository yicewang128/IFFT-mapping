# IFFT Mapping Project — v0.4.1

继续修改前请先读 [当前状态与修改入口](docs/CURRENT_STATE_zh.md) 和仓库根目录 AGENTS.md。

原始实数 signed IFFT 的彩色晶格显示，与 Gaussian(abs(IFFT)) 控制的透明度分开。
当前确认的默认 **连续 alpha** 参数：
- K₃SbS₃：T_low 为幅度数值 **0**（不是 P0），T_full=**P80**，即最亮20%完全显示。
- 五组 Sb：分别从各自的平滑幅度图计算 T_low=**P25**、T_full=**P99.5**，即最亮0.5%完全显示。
百分位作用于 Gaussian(abs(F))，不是原始 signed 灰度或显示亮度L。

## 当前流程

1. 每张 signed IFFT 的 P0.5/P99.5 定义显示窗口，标量 gamma=1。
2. 统一使用固定色调：RGB=round(L*color_rgb)，white_max=0；white_start=0.55 保留但不影响结果。
3. 对原始 signed IFFT 取 abs，然后 Gaussian sigma=5 px（reflect，truncate=4）。
4. 在同一张平滑幅度图 S 上选择 T_low、T_full：
   alpha=clip((S-T_low)/(T_full-T_low),0,1)。
5. 独立保存 RGB、float32 alpha、alpha8 和 RGBA；用 alpha8 合成黑底或 TEM 显示底图。

无 RMS、相关性、形态学、锐化、配准或输出重采样。默认不再使用 Otsu。
原图不改写；彩色图受窗口截断、LUT 和 RGB8 量化影响，定量分析使用原始 signed 数据。
详见 [方法](docs/METHODS_zh.md)、[v0.4.1变更](CHANGELOG.md)、[验证](docs/VALIDATION_zh.md)。

## Windows 运行

在项目目录（路径保留旧名称 IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project）打开终端：

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python src/review_mask.py
```

选择原始 IFFT。T_low 和 T_full 分别有滑块及数值输入；T_full 必须大于 T_low。
预览不自动保存，Save new run 才写入新目录。保存后的 effective_config.json 用绝对端点精确重放。
滑块是在当前图像幅度单位上操作；改变它会覆盖初始百分位设定。
原生 Windows 窗口尚未在本环境端到端验证；初始化、控件变化及保存回调已做无界面测试。

命令行：
```powershell
python src/pipeline.py --input data/input_ifft.tif --output runs/preview --config configs/default.json
python src/pipeline.py --input data/input_ifft.tif --output runs/top5 --alpha-low-percentile 10 --alpha-full-percentile 95
python src/pipeline.py --input data/input_ifft.tif --output runs/manual_full --alpha-full-value 1800
```

“最亮5%完全显示”对应 full percentile=95，而不是5。端点均在 Gaussian(abs(F)) 上计算。
可选的 full=max 指平滑幅度S的最大值，与未经平滑的 abs(F).max 不同；当前默认使用上述百分位。
上述1800仅为命令格式示例，不是推荐参数。

## Sb 五个反射晶族

```powershell
python src/run_sb_batch.py --input-dir data/sb --output runs/sb_first_preview
```

输入目录每个晶族只能有一张匹配 `IFFT (hkl) Sb*.tif` 的图。
顺序为012、104、110、202、024；分别读 configs/sb_*.json。
颜色：012宝蓝、104珊瑚红、110紫罗兰、202明黄、024亮橙；配置中的 RGB 是基色，颜色名称也来自同一配置。
每张独立采用 signed P0.5/P99.5 显示、幅度 P25→P99.5 alpha。可以单独运行：
```powershell
python src/pipeline.py --input "data/sb/你的012图.tif" --output runs/sb012 --config configs/sb_012.json
```

逐图归一化便于查看弱信号，**不同图显示亮度不代表绝对反射强度或相含量**。
脚本校验尺寸与标定相同，但不据此证明对齐或反射归属。不会把五张 signed IFFT 相加。
生成完整单图、每晶族左右对照（第一步/黑底连续alpha）、中心原像素裁剪和参数表。

## 已保存图层叠加 TEM

```powershell
python src/overlay_saved_run.py --run runs/preview --tem data/original_tem.tif --output runs/on_tem --tem-window 100 1800
```

16/32-bit TEM 必须提供实际显示窗口；100/1800仅为示例。8-bit 可不提供。
脚本重用保存的 RGB 和 **05_alpha_uint8.tif**，不重新阈值，也不使用辅助二值 mask 代替渐变。
原始 TEM 不滤波、不改写，RGB8 合成结果不是原始32-bit定量图。
同尺寸只是对齐的必要条件；不自动配准。

## 输出与兼容性

| 文件 | 意义 |
|---|---|
| 00_signed_ifft_float32.tif | 原始float32数值副本，未压缩 |
| 01_linear_green_channel_float32.tif | 归一化显示标量L |
| 01_linear_green_rgb.tif / 01_linear_green.png | 第一步实际RGB，可为绿色或Sb配色 |
| 02_abs_ifft_float32.tif | 原始signed IFFT绝对值 |
| 03_abs_gaussian_float32.tif | sigma5平滑幅度 |
| 04_selection_mask_uint8.tif | alpha_float>0的辅助support mask；**不能代替连续alpha** |
| 05_alpha_float32.tif | [0,1]连续alpha，未压缩，分析参考 |
| 05_alpha_uint8.tif | round(255*alpha)，与透明PNG一致 |
| 05_selected_green_transparent.png | RGBA8透明图 |
| 06_selected_on_black_rgb.tif / .png | 按alpha8合成黑底 |
| 07_TEM_display_reference_rgb.tif | 可选固定TEM显示底图 |
| 08_green_on_TEM_rgb.tif / .png | 可选按alpha8合成TEM |
| effective_config.json / run_manifest.json | 实际窗口、端点、代码/数据哈希和验证记录 |

为兼容旧程序保留含 green 的历史文件名，实际颜色以配置和manifest为准。
float32 alpha与alpha8的完全透明/完全不透明比例可能略不同，manifest分别记录。
TIFF未压缩、PNG无损编码；独立图均保留原宽高和像素坐标，只有标注为overview的预览缩小。

旧版配置不含alpha时继续按二值threshold运行。
`configs/legacy_green.json` 为原版A；`configs/legacy_v020_D.json` 为D颜色+Otsu二值alpha。
`--threshold` 显式切换二值模式，不能与连续alpha参数同时指定。

## 记录与验证

实验数据与输出不提交GitHub，代码和配置在仓库保存。每次运行写新目录，避免覆盖。
历史运行文档描述各自版本；阈值复核见 [RUN_005](docs/RUN_005_zh.md)，当前颜色与图层合成验证见 [RUN_006](docs/RUN_006_zh.md)。
用 `git pull --ff-only` 更新已有clone，或下载新的GitHub代码ZIP。
不要在网页上传包含实验图片的完整结果包；网页上传不会遵守.gitignore。

```powershell
python -m pip install pytest
python -m pytest -q
```

TIFF和独立alpha用于ImageJ/DM交换；ImageJ不一定保留PNG透明度。
[跨软件说明](docs/ImageJ_DigitalMicrograph_zh.md)与导入宏只读取Python输出，不重新推导边界。


## 六层黑底叠加（v0.4.1）

```powershell
python src/run_combined.py --k3 data/k3.tif --sb-dir data/sb --output runs/all_six
```

生成各层第一步RGB、RGBA、float32 alpha、黑底PNG与未压缩TIFF，以及Sb五层/全部六层黑底和透明合成。
默认先将五组Sb按alpha加权混色，组合alpha=1-product(1-alpha_i)，再把Sb组以普通source-over放在matrix上方。
图层从下到上：黑底、K3SbS3、Sb组合。显示覆盖不代表物理深度或matrix不存在；混色不表示新相。
具体公式和数值量化见 [当前状态](docs/CURRENT_STATE_zh.md)。仅检查尺寸和标定，不自动配准。

历史相加模式可显式使用：
```powershell
python src/run_combined.py --k3 data/k3.tif --sb-dir data/sb --output runs/additive --compositing additive
```

相加模式仍记录通道截顶比例；它没有上下图层关系，也不生成组合透明PNG。
默认更新会改变组合图视觉效果，但每层原始IFFT、alpha算法与确认的端点设置不变。

生成颜色图例、六层概览和可选的同位置新旧对照（只缩小预览，不改变完整图）：
```powershell
python src/preview_combined.py --run runs/all_six --output runs/previews
python src/preview_combined.py --run runs/all_six --output runs/compare --reference runs/previous --crop 768 768 512
```
参考目录使用run_combined的输出文件名。`--crop X Y SIZE`可重复，坐标为从0开始的左上角，局部保留原生像素。

