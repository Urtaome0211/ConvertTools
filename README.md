# 🧰 ConvertTools · 扁平化格式转换工具箱

一个基于 **Python 3 + PySide6 (Qt 6)** 的本地桌面格式转换工具，扁平化界面风格，共 13 项转换功能，所有转换均在本地完成，文件不会上传网络。当前版本 **v1.1.0**。

> 🔗 源码仓库：<https://github.com/Urtaome0211/ConvertTools> ｜ 📥 下载单文件版：<https://github.com/Urtaome0211/ConvertTools/releases>

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Qt](https://img.shields.io/badge/Qt-6%2F%20PySide6-green) ![License](https://img.shields.io/badge/License-MIT-orange)

## ✨ 功能一览

| 功能 | 输入 | 输出 | 实现方式 |
| --- | --- | --- | --- |
| 📄 PDF ⇄ Word | .pdf / .docx · .doc | .docx / .pdf | pdf2docx 库 / MS Word COM |
| 🖼️ PDF ⇄ 图片 | .pdf / .png · .jpg … | .png · .jpg / .pdf | PyMuPDF 渲染 / Pillow 合成 |
| 📊 Excel ⇄ PDF | .xlsx · .xls / .pdf | .pdf / .xlsx | MS Excel COM / pdfplumber 表格提取 |
| 🎬 视频格式转换 | .mp4 · .mkv · .avi · .flv … | .mp4 · .mkv · .avi · .flv | ffmpeg（H.264 + AAC / MPEG-4 + MP3） |
| 🧩 多 PDF 合并 | 多个 .pdf | 单个 .pdf | PyMuPDF，支持拖拽排序 |
| 🎵 音视频分离 / 合并 | 视频 / 视频+音频 | 音频 · 无声视频 · 合成视频 | ffmpeg 流复制 / 重编码 |
| 🗜️ PDF 压缩 | .pdf | .pdf | 无损优化 / 有损重渲染（DPI + JPEG） |
| ✂️ PDF 拆分 | .pdf | 多个 .pdf | 每页 / 每 N 页 / 自定义页码范围 |
| 🔒 PDF 加密 / 解密 / 水印 | .pdf | .pdf | AES-256 口令加密 / 文字与图片水印 |
| 🖌️ 图片格式互转 | .png · .jpg · .webp · .bmp · .tiff | 同上五种格式 | Pillow，支持缩放与压缩质量 |
| 🎧 音频格式互转 | .mp3 · .wav · .aac · .m4a · .flac · .ogg | 同上六种格式 | ffmpeg（码率可调） |
| 📉 视频压缩 | 常见视频格式 | .mp4 | ffmpeg H.264 + AAC，画质与分辨率可调 |
| 🎞️ 视频转 GIF | 常见视频格式 | .gif | palettegen + paletteuse 两遍调色板 |

**通用特性**：批量处理（单文件失败不中断）· 拖拽添加文件 · 实时进度条与日志 · 可选自定义输出目录 · 转换过程可随时取消 · 自动记住上次参数 · 完成后提示音 + 结果弹窗（可一键打开输出文件夹）。

## 📁 项目结构

```
convertTools/
├── main.py                     # 程序入口
├── requirements.txt
├── app/
│   ├── __init__.py             # 版本号
│   ├── style.py                # 扁平化 QSS 样式
│   ├── main_window.py          # 主窗口（侧边导航 + 功能页堆栈）
│   ├── workers.py              # 后台线程 TaskWorker（进度/日志/取消）
│   ├── core/                   # 纯逻辑层（无 UI 依赖）
│   │   ├── ffmpeg.py           # ffmpeg 查找、进度解析、命令执行
│   │   ├── video.py            # 视频转换 / 音视频分离合并
│   │   ├── office.py           # Word/Excel → PDF（COM 自动化）
│   │   ├── pdf_word.py         # PDF → Word
│   │   ├── pdf_image.py        # PDF ⇄ 图片
│   │   ├── pdf_merge.py        # 多 PDF 合并
│   │   ├── xlsx_pdf.py         # PDF → Excel
│   │   ├── pdf_compress.py     # PDF 压缩（无损 / 有损）
│   │   ├── pdf_split.py        # PDF 拆分（单页 / 每 N 页 / 范围）
│   │   ├── pdf_security.py     # PDF 加密 / 解密 / 水印
│   │   ├── image_convert.py    # 图片格式互转与缩放
│   │   ├── audio_convert.py    # 音频格式互转
│   │   ├── video_compress.py   # 视频压缩 / 改分辨率
│   │   ├── gif_make.py         # 视频转 GIF
│   │   └── utils.py            # 体积格式化等小工具
│   └── ui/
│       ├── base.py             # 功能页基类（拖放/进度/日志骨架）
│       ├── widgets.py          # DropZone 拖放控件
│       └── pages/              # 各功能页（每页一个文件）
├── tools/                      # 便携版 ffmpeg.exe / ffprobe.exe（可选）
└── tests/smoke_test.py         # 端到端冒烟测试
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备 ffmpeg（视频/音频功能需要）

两种方式任选其一（或都装，程序会自动优先使用 `tools/` 下的便携版）：

- **便携版**：把 `ffmpeg.exe` 与 `ffprobe.exe` 放到项目 `tools/` 目录（推荐，免安装）；
- **系统安装**：`winget install Gyan.FFmpeg` 或自行配置到系统 PATH。

### 3. 运行

```bash
python main.py
```

### 4. 运行测试（可选）

```bash
python tests/smoke_test.py
```

## 🖥️ 使用说明

1. 左侧导航栏选择功能；
2. 拖入文件或点击拖放区浏览选择（可多选）；
3. 按需调整参数（输出格式 / 画质 / DPI / 输出目录等）；
4. 点击 **开始转换**，右侧实时显示进度与日志；
5. 输出文件默认与原文件同目录，可在界面中勾选自定义输出目录；
6. 转换完成后会有提示音与结果弹窗，可一键打开输出文件夹（可在弹窗中关闭成功提示、仅保留提示音）；
7. 各功能的参数（模式、格式、画质等）会自动记住，下次启动自动恢复。

## ⚙️ 关键依赖与环境要求

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| PySide6 | ≥ 6.10 | Qt 6 界面 |
| PyMuPDF | ≥ 1.24 | PDF 渲染 / 合并 |
| pdf2docx | ≥ 0.5.8 | PDF → Word |
| pdfplumber | ≥ 0.11 | PDF → Excel 表格提取 |
| openpyxl | ≥ 3.1 | 读写 .xlsx |
| Pillow | ≥ 11 | 图片处理 |
| pywin32 | ≥ 312 | Word/Excel COM 自动化（仅 Windows） |

- **操作系统**：Windows 10/11（Word/Excel → PDF 依赖本机安装的 Microsoft Office）；
- **ffmpeg**：视频、音频相关功能必需（见上文安装方式）。

## 📦 打包发布（可选）

单文件 exe（内置便携版 ffmpeg，目标机器无需安装任何依赖）：

```bash
pyinstaller --noconfirm --clean --onefile --windowed --name ConvertTools `
  --add-data "app;app" `
  --add-binary "tools\ffmpeg.exe;tools" `
  --add-binary "tools\ffprobe.exe;tools" `
  --add-binary "C:\Program Files\Python315\abi3t-compat\python3t.dll;." `
  --hidden-import fitz --hidden-import pymupdf `
  main.py
```

产物在 `dist/ConvertTools.exe`。打包后可执行 `ConvertTools.exe --selftest` 做无界面自检（退出码 0 表示通过，日志写入 `%TEMP%\convertTools_selftest.log`）。

> 说明：
> - Word/Excel → PDF 仍需要目标机器安装 Microsoft Office；视频/音频功能已随 exe 内置 ffmpeg，无需单独安装。
> - `abi3t-compat\python3t.dll` 是 Python 3.15 为 abi3t 扩展（如 cryptography）提供的兼容垫片，不打包会导致 pdfplumber 无法加载；用其他 Python 版本打包时如无此文件可省略该行。
> - 单文件模式首次启动需解压（约 318 MB，含 ffmpeg），启动约需数秒；如需秒开，可去掉 `--onefile` 改为目录模式发布。

## ⚠️ 已知限制

- **Word/Excel → PDF**：依赖本机安装 Microsoft Office；转换时后台调用 Office 组件（首次稍慢）。
- **PDF → Excel**：仅能提取 PDF 中的表格；扫描件、图片型 PDF 无法提取文字与表格。
- **PDF → Word**：排版复杂的 PDF 转换效果取决于版面结构，扫描件不可用。
- **视频转换**：avi 输出使用 MPEG-4 + MP3 编码以保证兼容性；其余格式为 H.264 + AAC。
- **PDF 有损压缩**：按 DPI 渲染为图片后重组，文字将被栅格化（不可再选中/搜索），适合扫描件；无损压缩保留文字层。
- **图片互转**：bmp / tiff 等无损格式输出体积较大，属正常现象。
- **视频转 GIF**：GIF 无帧间压缩，输出体积可能大于源视频，长片段建议降低帧率与宽度。

## 📄 License

MIT
