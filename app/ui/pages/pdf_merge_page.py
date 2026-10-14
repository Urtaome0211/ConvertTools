"""多 PDF 合并功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton

from app.core.pdf_merge import merge_pdfs
from app.ui.base import ConverterPage


class PdfMergePage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "多 PDF 合并",
            "按列表顺序将多个 PDF 合并为一个文件。选中条目后用 ↑ / ↓ 调整合并顺序。",
            exts=(".pdf",),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(8)
        self.btn_up = QPushButton("↑ 上移")
        self.btn_up.clicked.connect(lambda: self._move(-1))
        self.btn_down = QPushButton("↓ 下移")
        self.btn_down.clicked.connect(lambda: self._move(1))
        self.lbl_name = QLabel("输出文件名")
        self.edit_name = QLineEdit("合并结果.pdf")
        row.addWidget(self.btn_up)
        row.addWidget(self.btn_down)
        row.addSpacing(10)
        row.addWidget(self.lbl_name)
        row.addWidget(self.edit_name, 1)
        self.extra.addLayout(row)

        self._register_setting(self.edit_name, "out_name")

    def _move(self, delta: int):
        row = self.file_list.currentRow()
        if row < 0:
            return
        new_row = row + delta
        if not (0 <= new_row < self.file_list.count()):
            return
        item = self.file_list.takeItem(row)
        self.file_list.insertItem(new_row, item)
        self.file_list.setCurrentRow(new_row)

    def _valid_input(self, files):
        if len(files) < 2:
            QMessageBox.warning(self, "提示", "请至少添加 2 个 PDF 文件")
            return False
        name = self.edit_name.text().strip()
        if not name.lower().endswith(".pdf"):
            QMessageBox.warning(self, "提示", "输出文件名必须以 .pdf 结尾")
            return False
        return True

    def _build_task(self, files, out_dir):
        name = self.edit_name.text().strip()

        def task(on_progress, on_log, is_cancelled):
            out = (out_dir or Path(files[0]).parent) / name
            if out.resolve() in {Path(f).resolve() for f in files}:
                raise RuntimeError("输出文件不能与输入文件同名，请修改输出文件名")
            n = merge_pdfs(files, out, on_progress=on_progress, on_log=on_log, is_cancelled=is_cancelled)
            on_log(f"✓ 完成：已合并 {n} 个 PDF → {out}")
            return n, n

        return task
