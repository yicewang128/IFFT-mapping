# 处理方法与每一步的理由

## 数据和目标

输入为已经由指定反射重建出的实数signed IFFT，记作F(x,y)。本项目不重新选择FFT反射。
原始TIFF以字节不变的方式保存在data；处理结果另存。像素坐标原点为左上角，数组顺序(y,x)。

本版本要回答的是：按照给定的幅度准则，哪些位置应显示绿色IFFT？
不据此直接断言这些区域就是完整K3SbS3相范围，或轮廓就是物理晶界。

## 1. Signed灰度显示与D颜色映射（v0.2.0）

默认显示范围取原始signed IFFT全图的第0.5与99.5百分位，记为low、high。
L=clip((F-low)/(high-low),0,1)，标量gamma=1。
显式display_window优先；effective_config保存解析后的low/high以供精确重放。

D颜色：G=round(255L)，R=B=round(230*clip((L-0.55)/(1-0.55),0,1))。
0.55以下保持纯绿色；更高亮处逐渐接近RGB(230,255,230)。这是分段LUT，
不能说最终显示亮度完全线性。参数由color_map、white_start、white_max控制。

这仅改变每个像素的显示，不滤波、不锐化、不移动像素。范围外的正/负灰度都会在显示中截断，
因此不能声称彩色输出保留全部强度信息或频谱；非线性LUT和截断也可能引入谐波。
原始signed IFFT完整保留，晶格间距、强度或频谱分析使用原始数据。
本图D显示窗口约-3833.96至4638.92，全图两端各截断0.5%；选中区域合计约2.45%。
这提高可见度，不提高空间分辨率。一个图像只用一个全局窗口，不做局部对比度增强。
逐图百分位范围不能用于跨图绝对亮度比较；同系列可显式固定display_window。

旧版A仍可用configs/legacy_green.json：L=(F-Fmin)/(Fmax-Fmin)，RGB=(0,round(255L),0)。

仅在旧版A中，Fmin/Fmax为全图实际极值，无百分位裁切、直方图均衡或自动对比度增强。
这保持实数值的大小次序；负值、零、正值仍对应不同亮度。
零不一定映射到127.5：取决于显示窗口。旧版A本图约96.33/255，D约115.39/255。
仅未截断的仿射标量变换在浮点精度范围内只改变比例和DC；不能将此结论扩展到D彩色输出。
归一化float32通道与原始signed IFFT均保存，定量测量使用signed原图。
manifest报告全图两端及选中区域的截断比例，并记录颜色公式、窗口来源和实际值。

## 2. 取原始IFFT绝对值

B=abs(F)。必须对原始signed值操作，不能对已加正偏置的L取绝对值。

目的：正、负半周期都对“此处有条纹信号”贡献非负响应。
代价：符号被丢弃，周期条纹可能出现倍频。因此B只用于区域检测，不作为最终晶格显示。
此输入是实数灰度，不是包含独立实部/虚部的复数场。

## 3. 高斯平滑

S=G_sigma * B；sigma=5原始像素；SciPy mode='reflect'，truncate=4。
有限核半径为20px、每轴41个采样点；float64计算，float32中间TIFF导出。
它是局部加权平均绝对幅度，不是sqrt(G*(F^2))，因此不称为RMS。
目的：减少周期内亮暗起伏，让局部信号强弱用于区域选择。
平滑不施加在第一步绿色IFFT上。区域内用于显示的条纹不被Gaussian平滑。

本图像素尺寸为0.05192922428250313 nm/px，sigma约0.259646 nm。
Gaussian的FWHM约11.774px，即0.6114nm；这仅是本次平滑核宽度，
不等于总空间分辨率，更不等于晶界误差。先前FFT mask本身的展宽仍存在。
离图像外缘20px以内可能受所选reflect边缘延拓影响。

## 4. 区域选择

M=1 if S>=T else 0。初始T用4096-bin直方图Otsu得到。
Otsu最大化两类间方差，不是噪声显著性检验，不保证能选出所有弱晶格。
默认阈值只是可复现的初始设置：应检查native pixels、阈值敏感性和原始TEM。
可在GUI调T，或使用manual/percentile配置；最终应记录绝对T。
本版不填洞、不膨胀、不腐蚀、不删除小区域，不人工补全边界。
残余条纹或拍频可以令mask边缘带细齿或产生孔洞，本版如实保留以供审核。
threshold_sensitivity的±20%只是参数扰动示意，不是误差棒或置信区间。

## 5. 用mask显示第一步原始绿色条纹

RGBA=(RGB_step1, 255M)。这是二值alpha，不按S的强弱继续减弱域内亮度。
即使域内某像素在第一步为纯黑，它也保持alpha=255，不能按“黑色=透明”来删除。
因此本项目另存独立alpha/mask，不依赖ImageJ是否支持PNG透明通道。
mask以外的隐藏RGB可以非零，但alpha严格为零，标准RGBA查看器不显示它。

局部区域内的RGB与第一步完全一致；然而加mask后的整幅图的频谱会改变。
不能用已抠图的整体FFT作为原始衍射数据，也不能说阈值选择完全没有信息损失。
低于阈值的信号只是在此展示中隐藏，原始IFFT及幅度图仍完整保存。

## 6. 黑底或TEM底图

黑底：C_black=M*RGB_step1。
TEM：C=opacity*M*RGB_step1+(1-opacity*M)*TEM_display。

原TEM文件不改写；无锐化、滤波、背景扣除、配准或尺寸调整。
8-bit TEM使用原始显示值；16/32-bit必须提供DM/ImageJ显示窗口才能生成RGB显示。
高位深原始TEM不可能在RGB8合成图中保持其全部数值精度，原文件应独立保留。
alpha=1的选中区显示纯绿色IFFT，alpha<1是视觉混合，可在config中显式记录。

## 本版与前期RMS方法的区别

旧思路：局部RMS/WRMS可能连续控制透明度。当前流程：abs → Gaussian → 阈值 → 二值透明度。
当前不使用相关性加权，也没有通过原TEM对mask做自动纠正。
为忠实于此次要求，不自动加入任何这些附加判断。

## 文献与实现来源

- 当前具体组合是用户指定的探索性流程，不能作为已经在K3SbS3/Sb上验证的算法引用。
- Grachev et al., Scientific Visualization 8(5), 113–121 (2016): https://sv-journal.org/2016-5/10/index.php?lang=en 。支持彩色频率选择图及滤波展宽讨论，未证明本版Otsu阈值。
- Seyring et al., J. Mater. Res. 24, 342–346 (2009): https://doi.org/10.1557/JMR.2009.0071 。局部幅度用于纳米晶区域识别的方法背景；本版没有实现其逐角度扫环。
- SciPy Gaussian定义: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html
- ImageJ宏函数: https://imagej.net/ij/developer/macro/functions2.html

后续验证可增加：原TEM局部FFT核查、取向一致性、不同mask宽度稳定性。
这些应作为独立的新版本实现，不悄悄改变v0.1.0。
