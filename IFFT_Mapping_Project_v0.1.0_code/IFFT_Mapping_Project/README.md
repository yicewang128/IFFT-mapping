# IFFT Mapping Project — v0.2.0

本项目将 **signed IFFT 晶格显示** 与 **晶格信号区域选择** 分开。
Python 是计算的唯一基准；TIFF 和 mask 用于 ImageJ / DigitalMicrograph 交换。
当前版本按用户指定流程实现，不代表已验证的真实晶界检测。

## 本版本的流程

1. 原始 signed IFFT 用全图第0.5/99.5百分位确定显示范围；标量gamma=1，再用黑→绿→近白色LUT显示（D模式）。
2. 对原始 signed IFFT（不是第一步已归一化的绿色通道）取绝对值。
3. 对绝对值进行 Gaussian smoothing，sigma=5 **原始像素**。
4. 给平滑后的幅度指标设阈值，产生二值区域 mask。
5. 选中区域：显示第一步原来的绿色 RGB；未选中区域：alpha=0。
6. 导出透明 PNG、黑底 TIFF/PNG；有对齐的 TEM 时可导出 TEM 合成图。

每一步为什么这样做、数学定义及限制见 [docs/METHODS_zh.md](docs/METHODS_zh.md)。
跨软件操作见 [docs/ImageJ_DigitalMicrograph_zh.md](docs/ImageJ_DigitalMicrograph_zh.md)。
示例实测参数见 [docs/RUN_001_zh.md](docs/RUN_001_zh.md)。
v0.2.0原始IFFT复跑及D图核对见 [docs/RUN_002_zh.md](docs/RUN_002_zh.md)。

## D显示与原版A的切换

默认 `configs/default.json` 使用D：`display_percentiles=[0.5,99.5]`、
`color_map="green_white"`、`white_start=0.55`、`white_max=230`。
最高颜色是RGB(230,255,230)。标量gamma=1不等于最终颜色亮度完全线性：
显示范围外的灰度会截断，LUT分段变化，RGB8还有量化。原始数值不改写。
这提高条纹可见度，不提高空间分辨率。Gaussian、阈值及二值alpha不受显示参数影响。

恢复原版A的完整min/max纯绿色显示：

```powershell
python src/review_mask.py --config configs/legacy_green.json
```

明确设置 `display_window=[low,high]` 时优先于百分位。复现某次运行使用其
`effective_config.json`；比较同一实验系列可固定同一显示窗口，避免逐图自动窗口影响亮度比较。
项目仍在原来的 `IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project` 目录，
为保持已有路径可用未改目录名；实际程序版本以 `src/pipeline.py` 为准。

## 安装与运行（Windows）

推荐使用独立的 Python 3.12 环境。在解压的项目文件夹中打开终端：

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python src/review_mask.py
```

选择原始 IFFT，拖动 Threshold 滑块或输入 Exact T，观察区域变化。
图形工具栏的放大镜可用于查看晶格。点击 **Save new run** 后生成新运行文件夹。
关闭窗口不会自动保存。英文界面用于避免不同系统中文字体缺失。
首次安装完成后，也可在已配置的 Python 环境运行 `run_review_windows.bat`。

## 不打开界面，完整复现本次计算

完整存档包含 `data/input_ifft.tif`；纯代码包需要自行放入 TIFF。

```powershell
python src/pipeline.py --input data/input_ifft.tif --output runs/my_run_001 --config configs/default.json
```

默认 Otsu 是**待审核的初始区域选择**。改为绝对阈值，例如：

```powershell
python src/pipeline.py --input data/input_ifft.tif --output runs/my_run_002 --threshold 959.9598835876563
```

精确复现某次运行，使用该次 `effective_config.json`；尽量保持同样的依赖版本。
输出目录必须是新目录或空目录，避免覆盖旧结果。

## 叠加原始 TEM

输入必须已经与 IFFT 同位置、同尺寸、同像素采样；程序不会自动对齐或缩放。
同尺寸只是必要条件，不能证明两张图对齐。

8-bit 灰度或 RGB TEM 可以直接运行：

```powershell
python src/pipeline.py --input data/input_ifft.tif --output runs/with_tem --tem data/original_tem.tif --tem-opacity 1
```

如果 TEM 是 16-bit/32-bit，必须指定与 DM/ImageJ 当前显示一致的 min/max，例如：

```powershell
python src/pipeline.py --input data/input_ifft.tif --output runs/with_float_tem --tem data/original_tem.tif --tem-window 100 1800 --tem-opacity 0.6
```

**100、1800 仅是命令格式示例，不是建议的 TEM 显示范围。**
原始 TEM 文件从不被改写；合成图必然是新的 RGB 显示图。掩膜外与所记录的 TEM 显示图逐像素相同。
opacity=1 时域内完全显示绿色 IFFT，0.6 时域内混合绿色和 TEM；域外仍只有 TEM。
历史 `runs/run_001` 是不含TEM的v0.1.0运行；新运行请另建目录。

**已审核过mask后，优先直接使用保存结果，避免再次计算区域：**

```powershell
python src/overlay_saved_run.py --run runs/run_001 --tem data/original_tem.tif --output runs/approved_on_tem --opacity 1
```

高位深TEM同样需添加 `--tem-window MIN MAX`。这个脚本完全复用所选run的绿色图和mask。

## 结果文件

| 文件 | 意义 |
|---|---|
| `00_signed_ifft_float32.tif` | 原始32-bit数值的无压缩副本；原文件另存于data |
| `01_linear_green_channel_float32.tif` | 显示窗口归一化并截断后的标量L，0–1；普通Green LUT不能复现D颜色 |
| `01_linear_green_rgb.tif` / `.png` | 第一步实际配色，RGB8；D使用green-white LUT，标量gamma=1 |
| `02_abs_ifft_float32.tif` | 原始signed IFFT的绝对值 |
| `03_abs_gaussian_float32.tif` | Gaussian(abs(IFFT))，原始灰度单位 |
| `04_selection_mask_uint8.tif` | 选中255，未选中0；不是原始图像强度 |
| `05_alpha_uint8.tif` | 透明度的独立通道，当前与mask一致 |
| `05_selected_green_transparent.png` | 真正RGBA透明图；棋盘格不写入该文件 |
| `06_selected_on_black_rgb.tif` / `.png` | 同一绿色图层显示在黑底 |
| `07_TEM_display_reference_rgb.tif` | 可选；记录用于合成的TEM显示版本 |
| `08_green_on_TEM_rgb.tif` / `.png` | 可选；TEM合成图 |
| `overview.png` | 六步缩略预览，不用于测晶格间距 |
| `native_crop_gray_green_selected.png` | 中心512×512原始像素裁切，三幅横排 |
| `threshold_sensitivity.png` | 0.8T、T、1.2T探索比较，不是置信区间 |
| `effective_config.json` | 已解析的显示范围及绝对阈值，用于复现 |
| `run_manifest.json` | 输入/输出哈希、代码哈希、版本、采样、参数与检查记录 |

所有分析 TIFF 和独立结果 PNG 保持输入宽高，未旋转/重采样。
保留 `linear_green` 历史文件名以兼容导入脚本；实际配色和截断比例以manifest为准。
TIFF 无图像压缩；PNG 的压缩无损，但 RGB 显示本身是8-bit量化。
原始32-bit signed IFFT用于晶格定量分析；显示标量L及RGB可能有截断，不代替原始数据。ZIP只是无损打包。

## 可复现与 GitHub

建议用 Python 管理算法与参数，用 ImageJ/DM 查看 TIFF、检查 ROI。
跨软件直接重新计算 Gaussian/阈值可能有边缘处理和浮点差异；直接导入本项目输出最一致。

已经用git clone获取仓库时，在仓库目录运行 `git pull --ff-only` 更新。
若使用GitHub网页下载ZIP，请下载新版本并在新目录解压，保留旧运行记录。

`.gitignore` 排除 `data/` 实验图片及 `runs/` 输出，代码和说明可以独立版本控制。
**不要在 GitHub 网页一次性上传完整存档中的所有文件：网页上传不会自动遵守 .gitignore。**
代码仓库：https://github.com/yicewang128/IFFT-mapping 。实验图片与运行输出单独保留。
每次改变参数都生成新run；确认后的阈值可保存成新的 `configs/*.json` 并提交。
科研数据与代码的公开许可由项目所有者决定，本包未预先指定开源许可证。

## 验证

```powershell
python -m pip install pytest
python -m pytest -q
```

测试涵盖旧版仿射显示周期、abs/平滑顺序、非RMS、透明度、TEM域外像素、原文件不改写及TIFF标定，
并验证D显示不会改变mask、effective配置可重放、交互预览与保存结果一致。
这些是计算/文件正确性检查，不是晶界真实性的验证。
交互预览的初始化及保存回调已做程序化检查。ImageJ导入宏尚未完成图形环境端到端验证；
DigitalMicrograph未在本环境运行。不要将跨软件可读的数据格式误解为所有软件版本已通过测试。

可选Jupyter逐步操作：`notebooks/Walkthrough.ipynb`；需另外安装 `jupyterlab`。
