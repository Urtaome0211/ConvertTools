# ConvertTools v1.1.0 发布说明

一个基于 **Python 3 + PySide6 (Qt 6)** 的本地桌面格式转换工具箱：扁平化界面、无广告、文件全程本地处理。本版本共 **13 项转换功能**，单文件 exe 内置 ffmpeg，目标机器无需安装任何依赖。

## 🆕 本版新增（v1.1.0）

- 🗜️ **PDF 压缩**：无损优化 / 有损重渲染（DPI + JPEG），完成后对比前后体积
- ✂️ **PDF 拆分**：每页一文件 / 每 N 页一组 / 自定义页码范围（如 `1-3,5,7-`）
- 🔒 **PDF 加密 / 解密 / 水印**：AES-256 口令加密；文字或图片水印（透明度 / 字号 / 角度可调）
- 🖌️ **图片格式互转**：jpg / png / webp / bmp / tiff，质量与 5 种缩放模式
- 🎧 **音频格式互转**：mp3 / wav / aac / m4a / flac / ogg，码率可调
- 📉 **视频压缩**：H.264 + AAC，CRF 画质档 + 分辨率（不缩放 / 1080p / 720p / 480p / 自定义宽度），对比前后体积
- 🎞️ **视频转 GIF**：palettegen + paletteuse 两遍调色板，fps / 宽度 / 起止时间可调
- ✨ **体验改进**：所有页面自动记住上次参数（QSettings）；转换完成提示音 + 结果弹窗（一键打开输出文件夹，可关闭成功弹窗仅保留提示音）

## 📦 基础功能（v1.0）

- 📄 PDF ⇄ Word（pdf2docx / MS Word COM）
- 🖼️ PDF ⇄ 图片（PyMuPDF / Pillow，DPI 可调）
- 📊 Excel ⇄ PDF（MS Excel COM / pdfplumber 表格提取）
- 🎬 视频格式转换（mp4 / mkv / avi / flv）
- 🧩 多 PDF 合并（拖拽排序）
- 🎵 音视频分离 / 合并（ffmpeg）

**通用特性**：批量处理（单文件失败不中断）· 拖拽添加 · 实时进度与日志 · 自定义输出目录 · 可随时取消。

## 🖥️ 系统要求

- Windows 10/11（64 位）
- Word/Excel → PDF 功能需要本机安装 Microsoft Office
- 其余功能开箱即用（视频 / 音频功能已内置 ffmpeg）

## 🔍 校验

- 文件名：`ConvertTools.exe`
- SHA-256：`C61A9ADB6FF666D136712219ABA5A83D2202972A811E979D5378B42206A7C7D9`
- 大小：约 318 MB（333,380,498 字节）

## 📄 说明

- 首次启动需解压内置组件，约需数秒。
- 源码见仓库 `app/` 目录（MIT 协议）；`tests/smoke_test.py` 可一键回归全部功能。
