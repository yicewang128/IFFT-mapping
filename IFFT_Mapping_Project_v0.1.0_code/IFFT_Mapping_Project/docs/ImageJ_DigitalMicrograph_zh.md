# Python、ImageJ与DigitalMicrograph如何配合

## 为什么选Python做主程序

Python适合明确记录数组运算、参数、依赖版本和测试，也适合GitHub。
ImageJ宏适合图像窗口、LUT和ROI操作；DM脚本依赖DM环境，直接跨软件复用不便。
本版不依赖DM内置Python，不承诺任意DM版本可直接运行Python源文件。
跨软件的共同数据接口是TIFF、二值mask和参数JSON，而不是一种三者通用的脚本语言。

## ImageJ/Fiji打开本次结果

1. Plugins > Macros > Run，选择 `imagej/Open_Processed_Run.ijm`。
2. 选择 `runs/run_001` 或自己的新run目录。
3. 宏打开signed原图、float32绿色LUT图、平滑幅度图、黑底图和mask。
4. mask转换成复合ROI，添加到ROI Manager。
5. 可选打开已对齐TEM，添加绿色**轮廓Overlay**；不改TEM像素。

导入宏只读取Python计算结果，没有另算Gaussian/Otsu，因此mask相同。
若不是float32输入，步骤00可能是NPY而不是TIFF，此导入宏只适用于当前float32流程。
ROI轮廓是区域选择边缘，不自动等于物理晶界。

## 为什么透明PNG在ImageJ里可能变黑

ImageJ1通常将RGB与overlay/ROI分开管理；PNG的alpha不一定在打开/复制后保留。
不能把“RGB黑像素透明化”等同于正确alpha，因为真正的条纹负峰也可能是黑色。
精确彩色TEM合成以Python为基准，或者在支持RGBA的figure软件中叠加透明PNG。
在ImageJ内需要查看选择位置时使用导入宏的mask/ROI；需要最终合成图时打开Python的08文件。

## DigitalMicrograph

- 打开 `00_signed_ifft_float32.tif`：查看原始signed数值。
- 打开 `03_abs_gaussian_float32.tif`：查看区域检测指标。
- 打开 `04_selection_mask_uint8.tif`：查看二值选择位置。
- 打开 `06_selected_on_black_rgb.tif` 或可选的 `08_green_on_TEM_rgb.tif`：查看已经生成的RGB图。
- `01_linear_green_channel_float32.tif` 范围0–1；若在DM手动上色，应设线性黑→绿及显示0–1。

这些是单帧标准TIFF；输出写入ImageJ标定和Gatan像素尺寸标签，并在manifest记录标定。
本环境未运行DigitalMicrograph，因此不能宣称已验证DM界面或所有版本的标定读取。
首次打开应检查尺寸2048×2048、像素尺寸0.05192922428250313 nm/px；
若软件未读取标定，按manifest手动设置，不能用72dpi代替真实nm/px。

## 在figure软件里做透明叠加

将TEM和 `05_selected_green_transparent.png` 设置同样宽高、同样位置，不裁切、不旋转。
绿色图层置于TEM上层。需要保持二值选区内原色时，图层整体opacity设100%。
棋盘格仅出现在overview预览，透明PNG本身没有棋盘格。
为后续量化继续保留32-bit原图；RGB/PNG是显示文件。
