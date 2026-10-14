"""主窗口：左侧图标导航栏 + 右侧功能页堆栈。"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app import __version__
from app.ui.pages.about_page import AboutPage
from app.ui.pages.audio_page import AudioPage
from app.ui.pages.av_page import AvPage
from app.ui.pages.gif_page import GifPage
from app.ui.pages.image_page import ImagePage
from app.ui.pages.pdf_compress_page import PdfCompressPage
from app.ui.pages.pdf_image_page import PdfImagePage
from app.ui.pages.pdf_merge_page import PdfMergePage
from app.ui.pages.pdf_security_page import PdfSecurityPage
from app.ui.pages.pdf_split_page import PdfSplitPage
from app.ui.pages.pdf_word_page import PdfWordPage
from app.ui.pages.video_compress_page import VideoCompressPage
from app.ui.pages.video_page import VideoPage
from app.ui.pages.xlsx_pdf_page import XlsxPdfPage

NAV_ITEMS = [
    ("📄", "PDF ⇄ Word", PdfWordPage),
    ("🖼️", "PDF ⇄ 图片", PdfImagePage),
    ("📊", "Excel ⇄ PDF", XlsxPdfPage),
    ("🎬", "视频格式转换", VideoPage),
    ("🎵", "音视频分离 / 合并", AvPage),
    ("🧩", "多 PDF 合并", PdfMergePage),
    ("🗜️", "PDF 压缩", PdfCompressPage),
    ("✂️", "PDF 拆分", PdfSplitPage),
    ("🔒", "PDF 加密 / 水印", PdfSecurityPage),
    ("🖌️", "图片格式转换", ImagePage),
    ("🎧", "音频格式转换", AudioPage),
    ("📉", "视频压缩", VideoCompressPage),
    ("🎞️", "视频转 GIF", GifPage),
    ("ℹ️", "关于", AboutPage),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ConvertTools · 格式转换工具箱")
        self.resize(1020, 720)
        self.setMinimumSize(920, 640)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 左侧导航
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        s_lay = QVBoxLayout(sidebar)
        s_lay.setContentsMargins(0, 14, 0, 10)
        s_lay.setSpacing(0)
        brand = QLabel("🧰  ConvertTools")
        brand.setObjectName("brand")
        s_lay.addWidget(brand)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setIconSize(QSize(20, 20))
        for icon, name, _ in NAV_ITEMS:
            self.nav.addItem(QListWidgetItem(f"{icon}  {name}"))
        self.nav.currentRowChanged.connect(self._switch_page)
        s_lay.addWidget(self.nav, 1)
        ver = QLabel(f"v{__version__}")
        ver.setObjectName("ver")
        ver.setAlignment(Qt.AlignCenter)
        s_lay.addWidget(ver)
        root.addWidget(sidebar)

        # 右侧功能页
        self.stack = QStackedWidget()
        for _, _, page_cls in NAV_ITEMS:
            self.stack.addWidget(page_cls())
        root.addWidget(self.stack, 1)

        self.nav.setCurrentRow(0)

    def _switch_page(self, row: int):
        if 0 <= row < self.stack.count():
            self.stack.setCurrentIndex(row)
