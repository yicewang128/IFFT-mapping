# v0.4.0 验证

20项测试通过，包括新增的透明层无贡献、单层保持、Sb排列不变性、union alpha、完全不透明上层遮盖下层、半透明source-over方向和输入尺寸/类型拒绝。
使用仓库run_combined命令对六张原始2048×2048 float32 IFFT完成真实运行。
每层alpha8与v0.3.2确认图逐像素相同；matrix的整张RGBA不变；所有原始源SHA256匹配。
用旧配色图层重放新compositing模块，与先前“Sb在上”预览的组合RGBA/黑底逐像素一致。
新结果的两张组合透明PNG铺黑底与导出黑底PNG一致；TIFF未压缩、尺寸与标定保留。
src/preview_combined.py完成图例、整体及两个原生局部新旧配色对照。预览缩小不影响完整输出。
详细运行记录见RUN_006_zh.md。Windows、ImageJ、DigitalMicrograph原生GUI尚未端到端实测。

## v0.3.2 验证

16项现有测试通过。六张原始2048×2048实数float32 IFFT使用更新后的配置重新计算显示、abs/Gaussian、连续alpha和单层渲染。
每张的实际端点、RGBA和黑底像素与已确认的K3 top20 / Sb P25→P99.5预览完全一致；源文件SHA256未改变。
实际端点和源哈希见 confirmed_endpoints_v032.json；流程见 RUN_005_zh.md。
本次没有改动叠加算法，也没有重跑Windows、ImageJ或Digital Micrograph原生GUI。

## v0.3.1 验证

16项测试通过。新增合成检查：uint8溢出、透明像素、图层顺序、尺寸拒绝，以及只在累加末尾量化。
六张真实IFFT运行时逐张检查源文件哈希、PNG解码像素一致性。
默认值更新不改变abs/Gaussian或显示窗口算法。GUI此前无界面测试通过，本次没有原生Windows端到端验证。

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

