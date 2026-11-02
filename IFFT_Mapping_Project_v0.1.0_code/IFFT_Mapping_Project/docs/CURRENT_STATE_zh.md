# 当前状态与后续修改入口 — v0.4.1

本文件是继续此项目的入口。旧聊天及历史RUN文档不覆盖这里的当前配置；用户后续明确指令优先。

## 目标与输入

把同位置的 K₃SbS₃ matrix IFFT 和五组 Sb 反射族 IFFT 显示为彩色晶格条纹，导出独立透明层、黑底图与叠加图。
颜色对应 {012}、{104}、{110}、{202}、{024} 反射族，不等于五颗粒子的唯一身份。
原始文件是有正负值的实数二维IFFT。当前数据为2048×2048 float32，像素0.05192922428250313 nm。
输入必须已共用坐标系；同尺寸同标定不证明精确配准。
仓库只保存代码和记录，不含实验TIFF。需要重现图像时，另行提供六张原始IFFT，不能用聊天PNG替代。

## 已确认参数

| 材料/反射族 | 基色RGB | 颜色名 | T_low | T_full |
|---|---|---|---|---|
| K₃SbS₃ | [0,255,0] | 绿色 | 数值0 | P80 |
| Sb {012} | [70,110,255] | 宝蓝 | 自己的P25 | 自己的P99.5 |
| Sb {104} | [255,70,55] | 珊瑚红 | 自己的P25 | 自己的P99.5 |
| Sb {110} | [170,85,255] | 紫罗兰 | 自己的P25 | 自己的P99.5 |
| Sb {202} | [255,230,50] | 明黄 | 自己的P25 | 自己的P99.5 |
| Sb {024} | [255,128,0] | 亮橙 | 自己的P25 | 自己的P99.5 |

这些基色是L=1时的RGB，不是整个区域被填成的统一颜色。颜色方案为v0.4.1版本，可在保留阈值的情况下继续调整。
K3的P80表示最亮20%完全不透明；Sb的P99.5表示最亮0.5%完全不透明。P25不是幅度数值25，也不是25%最大值。

## 数据如何流动

1. `pipeline.prepare_ifft_display`：原始signed F各自取P0.5/P99.5，得到 L=clip((F-a)/(b-a),0,1)，gamma=1。
2. `pipeline.render_layers`：white_max=0，因此RGB=round(L*color_rgb)。不对显示条纹做Gaussian。
3. `pipeline.amplitude_map`：对原始F取绝对值，再Gaussian(sigma=5px, mode=reflect, truncate=4)。得到S；不是RMS。
4. `pipeline.choose_alpha`：在各自S全图上取端点，alpha=clip((S-low)/(full-low),0,1)。不是Otsu二值裁切。
5. 保存alpha_float32，alpha8=round(255*alpha)，输出RGBA8。黑底使用同一alpha8。
6. `compositing.group_rgba`：五组Sb内部 C=Σ(alpha_i*C_i)/Σalpha_i，A=1-Π(1-alpha_i)。无信号时C=A=0；不按晶面先后覆盖。
7. `compositing.source_over_rgba`：Sb组在上、matrix在下。A_out=A_Sb+A_K3*(1-A_Sb)；预乘颜色为C_Sb*A_Sb+C_K3*A_K3*(1-A_Sb)。除以A_out导出直通RGBA，再按alpha8铺黑底。

内部在已编码的RGB8显示通道上用float64计算，不进行sRGB线性光转换。组合层保存时量化；同导出RGBA铺黑底逐像素一致。每一步的数值精度和图层规则应在论文作图记录中保留。
加权混色及union opacity是明确的显示设计，不是物理强度求和或晶体存在概率。Sb覆盖绿色不证明matrix在那里不存在，也不代表真实深度。

## 从干净项目运行

进入 `IFFT_Mapping_Project_v0.1.0_code/IFFT_Mapping_Project`：

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q
python src/run_combined.py --k3 data/k3.tif --sb-dir data/sb --output runs/current
```

Sb目录每个晶族必须恰有一张 `IFFT (012) Sb*.tif` 等匹配文件（104、110、202、024同理）。
输入数据放置示例见 `data/README.md`。输出目录必须新建或为空。可加 `--config-dir` 使用另一套配置。
单图：`python src/pipeline.py --input data/k3.tif --output runs/k3 --config configs/default.json`。
批量Sb：`python src/run_sb_batch.py --input-dir data/sb --output runs/sb`。
`python src/review_mask.py`用于交互试验；若手动改变滑块，就覆盖该次运行的默认端点。
保留历史相加合成：同一run_combined命令加 `--compositing additive`。

## 找到应改的文件

| 要修改什么 | 入口 |
|---|---|
| 每组Sb颜色及名称 | configs/sb_*.json 的 color_rgb、color_name |
| K3/Sb暗端亮端 | configs/default.json、configs/sb_*.json 的 alpha |
| signed亮度或幅度计算 | src/pipeline.py |
| Sb内部混色、Sb在matrix上 | src/compositing.py |
| 六图批处理与输出 | src/run_combined.py |
| 图例、缩小概览与原生局部新旧对照 | src/preview_combined.py |
| 已保存图层叠加TEM | src/overlay_saved_run.py；显式指定高位深TEM显示窗口 |
| GUI阈值预览 | src/review_mask.py |

每个运行目录的run_manifest.json记录输入SHA256、尺寸标定、配置、实际阈值及代码哈希。保留此文件以重现具体图像。
当前六图已确认绝对端点见 `confirmed_endpoints_v032.json`；这些数值仅用于这一组数据核对，新输入会按配置重新算百分位。
历史版本记录见CHANGELOG和RUN_001至RUN_007。不要将历史D近白色、Otsu或0→max重新当作当前默认。

## 当前限制

程序不独立判断反射归属、真实晶界、粒径、相含量或取向角。不同反射独立归一化后不能比较绝对强度。
多层颜色会混合，Sb内部弱背景也可能叠加；颜色分离是视觉目标，不保证所有屏幕或色觉条件下同样清楚。
原生Windows、ImageJ和DM的GUI需在对应电脑验证；本项目可直接交换TIFF和RGBA PNG，但软件导入时可能忽略PNG透明度。


当前配色验证和8张未压缩TIFF重现记录见 [RUN_007](RUN_007_zh.md)。
