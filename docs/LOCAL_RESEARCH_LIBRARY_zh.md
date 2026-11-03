# 本地 TEM 资料库工具 v1.0.0

这是独立的文件整理工具；IFFT 显示算法仍为 v0.4.1，参数和颜色没有改变。

## 这次实际确认了什么

- GitHub 私有仓库 yicewang128/IFFT-mapping 可读写。
- 当前开发环境是云端 Linux，没有用户的 Windows C: 盘连接。
- 因此尚未验证 `C:\ChatGPT shared research database` 存在、可读或可写。不能以云端测试代替本机验证。
- 本工具不建立远程连接、不开放网络服务、不自动上传文件。把代码保存到 GitHub 也不会让 ChatGPT 获得本机权限。

## 最简单的 Windows 使用方法

1. 在 GitHub 仓库点击 Code → Download ZIP，解压完整仓库；也可更新现有本地 clone。
2. 需要 Python 3.10 或以上。双击仓库根目录 `START_RESEARCH_LIBRARY_WINDOWS.cmd`。
3. 粘贴现有目录 `C:\ChatGPT shared research database`，按 Enter。
4. 输入 `1` 检查目录访问；输入 `2` 创建分类目录并逐文件读取、生成索引。
5. 把需要分类的新文件放入资料库的 `00_Inbox`。输入 `3` 预览；输入 `4` 执行分类复制。
6. 后续新增资料可再次执行 `4` 和 `5`（更新索引）。本版本不是持续监听的后台服务。

源文件保持原位置和字节不变；因此复制分类会多占一份空间。相同目标内容重复运行会复用；同名不同内容生成带哈希后缀的新文件。原始TIFF不重新编码，不改变像素、压缩方式或标定。

如果程序提示 Python 缺失，先安装 Python，再重新运行；不需要为了本工具安装 IFFT 的科学计算依赖。
如果目录不存在，先在资源管理器中创建。`setup/check` 不会把错误路径悄悄当作已经存在的目录。
如果出现 Permission denied，请查看该目录的 Windows 访问权限或改用你有权限的目录；脚本不能绕过权限。

## PowerShell 命令

从解压后的仓库根目录运行（已安装 Python Launcher 时）：

```powershell
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" check
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" setup
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" organize
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" organize --apply
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" index
```

`check` 验证目录列举及临时文件的创建、写入、重读和清理；不代表所有资料均已读完。
`index` 流式读取所有符合扫描范围的文件并计算 SHA256；错误会列入报告并返回非零退出码。
读取成功仅表示文件字节可读取，不表示 TIFF/DM4/PDF 内容已被科学解析。
`setup` 执行 check、创建分类目录及 index；运行前目录必须存在。单独的 `init` 可显式创建新根目录。

## 自动分类规则及范围

只对 `00_Inbox` 里的文件分类复制（包含其普通子目录）。资料库内其他位置会被索引，但不会被自动挪动。

| 目录 | 分类规则 |
|---|---|
| 01_Literature/Unreviewed | 普通 PDF；尚未确认文献类型、主题或方法 |
| 02_TEM_Methods | 文件名含 manual、handbook、用户手册、操作手册的 PDF/TXT/MD |
| 03_Raw_Data/TEM | DM3/DM4/SER/EMD/MRC，或名称含 TEM/original/原始的图像；仍须核查其真实处理历史 |
| 04_Crystal_Structures | CIF |
| 05_Processing/FFT | 文件名含 FFT 的图像 |
| 05_Processing/IFFT | 文件名含 IFFT 的图像，优先于 FFT 规则 |
| 05_Processing/Masks | 文件名含 mask 的图像 |
| 05_Processing/Code | Python、ImageJ宏、DM脚本等，仅存放不执行 |
| 06_Results | 文件名含 overlay、mapping、panel、composite 的图像 |
| 90_Index | 每次运行新建的索引/分类记录目录 |
| 99_Unsorted | 文件名证据不足的其他文件 |

规则是按扩展名和文件名的初步分类，不会理解论文内容，也不会自动鉴定 K3SbS3 或 Sb。
冲突优先级：结果 → mask → IFFT → FFT → 原始TEM。可在 `classify` 函数调整。
为限制扫描范围，跳过隐藏项、链接/Windows junction及其他reparse point、.git、虚拟环境、缓存及90_Index。
如资料位于云盘占位符或junction目录，可能被排除；先使用实际本地普通文件或另行配置可信访问方式。

## 检索和读取

```powershell
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" search "K3SbS3"
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" search "forbidden" --contents
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" read "notes.txt"
```

默认搜文件名和相对路径；`--contents` 额外搜 UTF-8 文本（TXT、MD、CSV、JSON、CIF、PY、IJM等），返回行号。单个文本读取上限8MiB。
PDF正文不在上述全文检索范围内。按页读取 PDF 需要可选依赖：

```powershell
py -3 -m pip install pypdf
py -3 tools\research_library.py --root "C:\ChatGPT shared research database" read "01_Literature/Unreviewed/paper.pdf" --page 3
```

页码从1开始。扫描PDF无可提取文本时明确提示，不声称没有相关内容。PDF中的图、公式及定量结论仍需检查原页。程序不将原始TEM等二进制文件当文本输出。
每次 index 生成新的 `catalog.json` 和 Excel可打开的UTF-8 BOM `catalog.csv`，保留历史记录。索引含文件路径与SHA256；没有论文全文。

## 让后续 ChatGPT/Codex 优先读取这个库

在实际支持本地访问的桌面应用/本地Codex中打开该资料库目录，授予访问权限并新建任务。先让它列文件、读指定文献页，确认真实访问。
初始化在资料库根目录创建 AGENTS.md（已有文件则保留），记录“先搜本地、引用原始来源、区分证据与推断”的规则。
如果库放在另一个代码项目之外，需在实际应用中把该目录加入允许访问的来源；AGENTS.md文字本身不会授予文件权限。
云端聊天、GitHub连接、本地执行是三件不同的事。只有目录已经挂载/授权给该次会话时，助手才可以读取它。单独把这份索引发给云端只提供目录信息，不提供原文件字节。
电脑离线、睡眠或执行程序未连接时，云端无法凭此脚本访问文件。不要把测试成功描述为永久远程连接。

## 验证

```powershell
py -3 -m unittest discover -s tools -p "test_research_library.py" -v
```

测试涵盖空格/中文路径、缺失目录、目录读写、完整哈希、复制保真、同名冲突、重复运行、失败状态、越界路径、链接/reparse point排除、文本检索与PDF依赖缺失。
Windows/Ubuntu GitHub Actions 使用临时合成文件测试。它们都不是用户电脑C盘的访问测试。
本次开发记录见 `docs/LOCAL_RESEARCH_LIBRARY_VALIDATION.json`。
