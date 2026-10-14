"""关于页面。"""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app import __version__


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        title = QLabel("关于 ConvertTools")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(8)

        lay.addWidget(QLabel(f"<b>ConvertTools v{__version__}</b> —— 扁平化格式转换工具箱"))
        lay.addWidget(QLabel("基于 Python 3 + PySide6 (Qt 6) 构建"))
        lay.addSpacing(6)
        for line in (
            "· PDF ⇄ Word（pdf2docx / MS Word COM 自动化）",
            "· PDF ⇄ 图片（PyMuPDF 逐页渲染 / Pillow 合成）",
            "· Excel ⇄ PDF（MS Excel COM 自动化 / pdfplumber 表格提取）",
            "· 视频格式转换（ffmpeg：mp4 / mkv / avi / flv）",
            "· 多 PDF 合并（PyMuPDF，支持拖拽排序）",
            "· 音视频分离 / 合并（ffmpeg 提取音轨、视频轨、重新合成）",
            "· PDF 压缩（无损优化 / 有损重渲染）",
            "· PDF 拆分（每页 / 每 N 页 / 自定义页码范围）",
            "· PDF 加密 / 解密 / 水印（AES-256 口令，文字与图片水印）",
            "· 图片格式互转（jpg / png / webp / bmp / tiff，可缩放与压缩）",
            "· 音频格式互转（mp3 / wav / aac / m4a / flac / ogg）",
            "· 视频压缩与分辨率调整（H.264，预设或自定义宽度）",
            "· 视频转 GIF（两遍调色板算法，可截取片段）",
        ):
            lay.addWidget(QLabel(line))
        lay.addSpacing(6)
        hint = QLabel(
            "依赖说明：视频与音频功能需要 ffmpeg（优先使用项目 tools/ffmpeg.exe，"
            "否则查找系统安装）；Word/Excel → PDF 需要本机安装 Microsoft Office。\n"
            "所有转换均在本地完成，文件不会上传网络。"
        )
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        root.addWidget(card)
        root.addStretch(1)
