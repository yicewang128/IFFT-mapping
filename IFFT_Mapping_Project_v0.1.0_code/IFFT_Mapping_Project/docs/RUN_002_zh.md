# v0.2.0：原始IFFT复跑与D显示验证

运行日期：2026-10-30。输入为最初项目使用的32-bit TIFF：
`IFFT mask K3SbS3 matrix of 400kX_OneView_200kV_2025-10-29-001 Debbie Bonded Wafer_0069(1).tif`。
输入SHA-256：`6cf05839c96f0ae3192d2dddabf79abd63fb54ebee3c612e966cc3a49b21c1a4`。
尺寸2048×2048，float32，采样0.05192922428250313 nm/pixel。

## 运行方式

将输入文件放到data/input_ifft.tif，在项目目录运行：

```powershell
python src/pipeline.py --input data/input_ifft.tif --output runs/run_002 --config configs/default.json
```

本次直接读取原始上传文件，不通过此前彩色输出或截图重建数据。
实验文件及大尺寸结果不随代码提交；完整结果另存并交付。

## 实测参数

| 参数 | 数值 |
|---|---|
| 原始min/max | -7103.220703125 / 11700.556640625 |
| D显示low/high | -3833.962907714844 / 4638.9210913085935 |
| 窗口规则 | 全图signed IFFT的0.5/99.5百分位 |
| 标量gamma | 1 |
| 颜色 | green_white，white_start=0.55，white_max=230 |
| 最高RGB | (230,255,230) |
| 原始零值对应G通道 | 115.38698530275734 / 255（量化前） |
| Gaussian | abs(F)，sigma=5px，reflect，truncate=4 |
| Otsu阈值 | 959.9598835876563，4096 bins |
| 选中比例 | 0.4075508117675781 |
| 全图显示截断比例 | 0.010000228881835938，两端各约0.5% |
| 选中区域显示截断比例 | 0.024537379372314833 |
| alpha | 选中255，域外0 |

## 检查结果

- 新版黑底RGB与此前独立D预览的全尺寸黑底RGB：逐像素完全相同，差异通道值数量0。
- 新版RGBA与此前独立D预览的全尺寸透明图：逐像素完全相同，差异通道值数量0。
- abs图、Gaussian图、mask和alpha与v0.1.0 run_001逐像素完全相同。
- 原始float32 TIFF数值与00输出逐像素一致；源文件SHA-256保持不变。
- 输出保留2048×2048及标定；TIFF均不压缩。
- 自动测试10项通过，含旧版行为、D参数、颜色与mask分离、有效配置重放、GUI预览与保存一致。

这些检查验证计算实现，不证明mask边缘是真实物理晶界。
ImageJ宏和DigitalMicrograph未做本机图形界面端到端验证。

## 与原始TEM叠加

另外将本次保存的RGB与mask直接叠加在已提供的同位置TEM上，opacity=1。
TEM显示窗口沿用前次的15506.1201171875至66232.1796875，gamma=1。
这仅用于32-bit TEM到RGB的显示；无锐化、空间滤波、配准或缩放。
不改变源TEM，mask外像素与TEM参考显示逐像素相同。

## 程序溯源

本次pipeline.py SHA-256：`54bc2c38ff9d9f4dcfd948afb5c23fa9526c81359ea495c79a813cb0591980d6`。
完整依赖版本、配置及源/输出哈希记录在交付的run_manifest.json中。
