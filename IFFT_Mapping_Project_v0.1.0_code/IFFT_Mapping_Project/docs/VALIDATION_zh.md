# 验证范围

## v0.3.0（2026-10-31）

14项测试通过，包含旧版兼容、连续端点/线性中点、颜色与alpha独立、保存重放、
saved-run TEM叠加与直接合成逐像素一致、GUI两个端点变化后保存与预览一致。
五张真实Sb float32图复跑，原输入哈希不变，所有独立输出保留2048×2048和采样标定。
图像RGB与第一步相同，PNG alpha8与独立alpha8相同。
这些是程序正确性检查，不证明反射归属、完全对齐、晶界或相含量。
Windows原生GUI、ImageJ及DM GUI没有端到端实测。

## v0.2.0（2026-10-30）


自动测试10项通过。新增显示窗口优先级、旧版兼容、green-white端点与alpha、
显示变更不影响abs/Gaussian/mask、effective_config精确重放，以及无显示器环境下
Matplotlib预览与保存图像一致性的检查。后者不等于Windows图形界面端到端测试。
原始2048×2048 IFFT复跑与此前D预览RGB/RGBA逐像素完全一致，详情见RUN_002_zh.md。




## v0.1.0历史记录

- Python：6项科学/文件不变量测试通过（pytest）。
- 交互查看器：构建界面、初始化阈值、触发Save new run回调并生成输出，程序化冒烟检查通过。
- 用户IFFT：2048×2048 float32原值副本与输入像素完全一致；输入文件SHA256不变。
- 选区内RGB与步骤1一致；选区外alpha=0；PNG alpha与mask逐像素一致。
- 所有分析输出宽高未改变；TIFF Compression=NONE。
- 模拟TEM测试：mask外与输入TEM显示逐像素相同；未更改输入TEM数组。
- 该项目没有原始TEM实图，尚未核查实际TEM/IFFT的配准和最终实图合成。
- ImageJ导入宏未完成GUI端到端运行；DigitalMicrograph未实测。
- 未验证物理晶界、相含量、反射归属、FFT mask是否正确。

程序正确性与物理解释应分别验证。

