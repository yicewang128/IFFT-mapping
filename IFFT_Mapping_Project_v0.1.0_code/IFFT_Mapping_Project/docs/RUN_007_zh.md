# RUN 007：确认 Sb {024} 亮橙配色，v0.4.1

用户确认亮橙预览后，将 configs/sb_024.json 的 color_rgb 设为 [255,128,0]、color_name 设为 bright orange。其余五层颜色不变。输入是六张原始 signed float32 IFFT，未从预览PNG反推数据。

## 保留参数与流程

- 每图 signed P0.5/P99.5 显示；gamma=1、white_max=0。
- 幅度为 Gaussian(abs(F)), sigma=5 px, reflect, truncate=4。
- K3：T_low=数值0、T_full=P80；每组Sb：自己的P25/P99.5。
- 五组Sb仍用alpha加权RGB/union opacity合为一层，再source-over放在绿色matrix上。
- 未裁剪、缩放、锐化或配准；完整输出2048×2048、0.05192922428250313 nm/pixel。

## 重现

在项目目录中使用六张原始输入（data/README.md）：

```bash
python -m pytest -q
python src/run_combined.py --k3 data/k3.tif --sb-dir data/sb --output runs/run_007
```

命令直接导出 K3SbS3_black.tif、Sb_012/104/110/202/024_black.tif、Sb_all_black.tif、K3SbS3_Sb_all_black.tif。交付文件添加 _uncompressed 后缀，字节不变。

## 验证结果

20项现有测试通过；六张原始文件SHA256与 confirmed_endpoints_v032.json 完全一致，处理前后不变。各自实际alpha端点也完全一致。
所有单层、Sb组合和最终组合的alpha8与v0.4.0逐像素相同；除024颜色外，其余五张RGBA全部相同。
024独立图、Sb组合图、Sb+K3组合图与用户确认的亮橙预览完整像素逐一相同。
全部8张交付TIFF均为Compression=NONE(1)，单页2048×2048 RGB8、原标定；每张像素与对应PNG以及RGBA铺黑底一致。每张12,583,328字节。具体哈希见 validation_v041.json。

TIFF为每通道8位、24位RGB的已渲染显示图；未压缩不等于原始float32强度。原始signed数据保留不动。没有标签或scale bar烧入像素。
Windows、ImageJ和DigitalMicrograph原生GUI未在本次端到端测试。颜色表示反射族，不代表唯一粒子身份；alpha和显示边界不构成物理晶界证明。
