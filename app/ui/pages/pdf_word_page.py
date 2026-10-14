"""PDF ⇄ Word 功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QRadioButton

from app.core.office import docx_to_pdf
from app.core.pdf_word import pdf_to_docx
from app.ui.base import ConverterPage
from app.workers import CancelledError


class PdfWordPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "PDF ⇄ Word",
            "PDF 转 Word 采用版面还原（pdf2docx）；Word 转 PDF 调用本机 MS Word，保真度最高。支持批量处理。",
            exts=(".pdf",),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(10)
        self.rb_p2w = QRadioButton("PDF → Word")
        self.rb_w2p = QRadioButton("Word → PDF")
        self.rb_p2w.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.rb_p2w)
        group.addButton(self.rb_w2p)
        self.rb_p2w.toggled.connect(self._on_mode_changed)
        row.addWidget(self.rb_p2w)
        row.addWidget(self.rb_w2p)
        row.addStretch(1)
        self.extra.addLayout(row)
        self._on_mode_changed()

        self._register_setting(self.rb_p2w, "mode")

    def _on_mode_changed(self):
        if self.rb_p2w.isChecked():
            self._set_exts((".pdf",))
        else:
            self._set_exts((".docx", ".doc"))

    def _build_task(self, files, out_dir):
        pdf_to_word = self.rb_p2w.isChecked()

        def task(on_progress, on_log, is_cancelled):
            total = len(files)
            ok = 0
            for i, f in enumerate(files):
                if is_cancelled():
                    raise CancelledError("任务已取消")
                on_log(f"[{i + 1}/{total}] {Path(f).name}")

                def sub(p, _i=i):
                    if p is None:
                        on_progress(None)
                    else:
                        on_progress(int((_i * 100 + p) / total))

                try:
                    if pdf_to_word:
                        out = self.output_path(f, ".docx", out_dir)
                        pdf_to_docx(f, out, on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
                    else:
                        out = self.output_path(f, ".pdf", out_dir)
                        docx_to_pdf(f, out, on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
                    ok += 1
                    on_log(f"✓ 完成：{out}")
                except CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001 - 单文件失败不中断批量
                    on_log(f"✗ 失败：{exc}")
                on_progress(int((i + 1) * 100 / total))
            if ok == total:
                return ok, total
            raise RuntimeError(f"完成：成功 {ok} / {total}，详见下方日志")

        return task
