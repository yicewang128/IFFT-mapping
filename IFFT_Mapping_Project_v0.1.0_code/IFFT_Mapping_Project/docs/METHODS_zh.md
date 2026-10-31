# v0.3.2 方法与参数的含义

## 两条独立处理路径

输入F是实数、有正负值的二维IFFT，不是复数场。本程序不重新选择FFT反射。
显示路径使用signed F；幅度路径使用abs(F)。原始文件不改写。
本方法显示“指定傅里叶分量的局部信号”，不自动证明相范围或物理晶界。

## 1. 晶格显示

每图独立取F的P0.5、P99.5为a、b：
L=clip((F-a)/(b-a),0,1)，标量gamma=1。
显式display_window优先；effective_config保存实际窗口。
显示保留正负值的大小次序，但两端裁切、LUT及RGB8量化会丢失显示强度细节，
所以不能声称彩色图保留全部频谱；定量测量使用原始F。

D绿色：G=round(255L)，R=B=round(230*clip((L-0.55)/0.45,0,1))。
v0.3.0通用颜色b_vec=color_rgb/255，最大分量须为1：
RGB=round(255*L*b_vec + W*(1-b_vec))，
W=white_max*clip((L-white_start)/(1-white_start),0,1)。
绿色b_vec=(0,1,0)退化到既有D公式；Sb五色使用同一规则。
当前默认white_max=0，因此RGB=round(L*color_rgb)，最高颜色是基色；上式仍可重现历史近白显示。完整颜色值在manifest中记录。gamma=1指标量，
不等于分段LUT的感知亮度完全线性。

这一阶段不计算alpha，也不平滑条纹。零灰度通常显示为中间颜色；
因此第一步未加alpha时，弱信号背景会带颜色，这是signed显示的预期行为。
逐图显示窗口不能直接比较不同反射的绝对强度。

## 2. 幅度

A=abs(F)，必须对原始signed数据操作，不能对已加偏置的L取abs。
对实数条纹取abs会丢弃符号并可能造成倍频，因此A不用于显示最终晶格。

S=Gaussian(A,sigma=5px,mode=reflect,truncate=4)，float64计算，float32 TIFF导出。
这是局部加权平均绝对幅度，不是RMS。核半径20px，每轴41个采样点。
sigma=5必须结合原像素尺寸报告；本次像素0.05192922428250313nm，sigma约0.259646nm。
平滑核宽度、原FFT mask引起的展宽及实际物理界面宽度不能混为一谈。

## 3. 连续alpha（本次更新）

所有百分位均在S的全图像素上计算，包含背景：
K₃SbS₃默认T_low=0（manual数值零，不是P0），T_full=P80(S)，即最亮20%完全显示。
五组Sb分别从自己的S计算T_low=P25(S)、T_full=P99.5(S)，即最亮0.5%完全显示。
这些是用户确认的显示参数，不是噪声标定或物理晶界判据。可通过配置或CLI覆盖。

alpha=clip((S-T_low)/(T_full-T_low),0,1)，alpha gamma=1。
S<=T_low完全透明，S>=T_full完全不透明，之间线性过渡。
“完全显示”保留第一步RGB，包括暗条纹；不是把整片区域涂成同一亮色。
T_full必须大于T_low，常数图或无效端点会报错。
不添加Otsu、相关性、RMS、形态学、自动填洞或手工修边。

透明比例是显示设计，不是已证明的无晶格比例。数值零暗端不会主动去除正幅度背景；
即使无可辨认晶格，噪声经abs和平滑后仍可能有微弱alpha。
alpha不是晶体存在概率，不是相含量，也不是晶界置信度。
每个晶族独立归一化不保证不同晶族的alpha能作绝对强度比较。

## 4. 保存与合成

RGB完全独立于alpha，逐像素与第一步相同，包括隐藏RGB。
alpha_float32.tif保留[0,1]权重；alpha8=round(255*alpha)与RGBA PNG一致。
量化会使极低alpha归零、极高alpha归一；manifest分别记录float与PNG端点比例。
黑底C=alpha8/255 * RGB。
TEM C=opacity*alpha8/255*RGB+(1-opacity*alpha8/255)*TEM_display。
合成用相同alpha8，确保透明PNG、黑底和saved-run叠加一致。
辅助04_selection_mask只记录alpha_float>0，不再是实际透明度。

原TEM文件不改写，不锐化、不滤波、不配准。高位深TEM只按显式指定显示窗转为RGB8；
RGB8结果不能替代原始32-bit数据。

## Sb分反射处理

五张输入来自用户分别提供的{012}、{104}、{110}、{202}、{024} IFFT。
逐张处理、逐张记录端点，不把五张signed图先相加，从而不额外引入相加抵消。
但每张若由整个环重建，仍包含该环内方向分量的叠加；本次没有重新分方向。
颜色只用于区分所选反射，归属采用输入标注，不是本代码独立验证晶相。
仅校验尺寸、标定和数值，不将同尺寸当作严格共定位证据。

## 文献背景与实现边界

Du et al., Nature Communications 16,8342(2025), https://doi.org/10.1038/s41467-025-62451-0
明确描述每对反射IFFT→实数绝对值→Gaussian sigma5px→三图RGB幅度合成，
并指出sigma随像素尺寸调整。它支持此幅度提取思路；
没有据此证明本项目的百分位端点设置或连续alpha应用回signed条纹是作者原算法。

Grachev et al., Scientific Visualization 8(5),113–121(2016),
https://sv-journal.org/2016-5/10/index.php?lang=en ，讨论彩色傅里叶分量显示与滤波展宽。
Seyring et al., JMR24,342–346(2009), https://doi.org/10.1557/JMR.2009.0071 ，提供局部幅度映射背景。
本项目没有实现其角度扫描，也不据这些文献声称已验证Sb/K3SbS3物理晶界。


## 六层相加显示

C=round(clip(sum_i(alpha8_i/255 * RGB_i),0,255))，按通道相加、只在末尾量化。
使用float64累加避免uint8溢出，与图层顺序无关。记录任一通道超过255的像素比例。
不把signed IFFT相加，不重新估算alpha，不按像素选择获胜晶族。
混色和白色只能表示显示信号叠加，不能据此判定一种新相或同一个颗粒的身份。
