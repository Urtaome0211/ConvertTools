"""自定义控件：可点击、可拖放的 DropZone。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout


class DropZone(QFrame):
    """点击浏览或拖放文件的虚线框。"""

    files_dropped = Signal(list)

    def __init__(self, exts=(), multi=True, parent=None):
        super().__init__(parent)
        self.exts = tuple(e.lower() for e in exts)
        self.multi = multi
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(110)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(4)

        self._title = QLabel("点击选择文件，或将文件拖到这里")
        self._title.setObjectName("dropTitle")
        self._title.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._title)

        self._sub = QLabel(self._ext_text())
        self._sub.setObjectName("hint")
        self._sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._sub)

    def set_exts(self, exts):
        """更新支持格式并刷新提示文本。"""
        self.exts = tuple(e.lower() for e in exts)
        self._sub.setText(self._ext_text())

    def _ext_text(self) -> str:
        return "支持格式：" + "  ".join(self.exts) if self.exts else "支持格式：不限"

    # ---------- 拖放 ----------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)

    # ---------- 点击 ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.browse()
        super().mousePressEvent(event)

    def browse(self):
        if self.multi:
            paths, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", self._filter())
        else:
            path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", self._filter())
            paths = [path] if path else []
        if paths:
            self.files_dropped.emit(paths)

    def _filter(self) -> str:
        exts = " ".join(f"*{e}" for e in self.exts)
        return f"支持的文件 ({exts});;所有文件 (*.*)"
