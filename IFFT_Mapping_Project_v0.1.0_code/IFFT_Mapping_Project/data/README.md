# 输入数据（不随代码仓库提供）

本仓库不包含实验TIFF。测试可不依赖实验数据运行；真实图像重现必须另行取得原始IFFT。
请使用同位置、同像素网格的实数signed IFFT，保持负值，不从已归一化RGB或截图反推。

推荐在项目目录下放置：

- data/k3.tif：K3SbS3 matrix的原始IFFT。
- data/sb/IFFT (012) Sb original.tif
- data/sb/IFFT (104) Sb original.tif
- data/sb/IFFT (110) Sb original.tif
- data/sb/IFFT (202) Sb original.tif
- data/sb/IFFT (024) Sb original.tif

Sb批处理匹配 `IFFT (hkl) Sb*.tif`；每组必须恰好一张。原文件已有匹配名称时无需改名。
K3通过--k3明确指定，任意文件名均可；所有路径可改为数据的实际位置。
如果复制数据，保留原件并校验SHA256。现有六图源哈希和确认端点见docs/confirmed_endpoints_v032.json。
当前参考数据是2048×2048 float32，像素0.05192922428250313nm。算法可读取其他标定的真实二维输入，但sigma5像素的物理长度会变化，必须重新评估。
默认忽略实验数据和runs；不要把实验图片或完整结果包直接上传GitHub。
