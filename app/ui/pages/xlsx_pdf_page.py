"""Excel ⇄ PDF 功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QRadioButton

from app.core.office import xlsx_to_pdf
from app.core.xlsx_pdf import pdf_to_xlsx
from app.ui.base import ConverterPage
from app.workers import CancelledError


class XlsxPdfPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "Excel ⇄ PDF",
            "Excel 转 PDF 调用本机 MS Excel，保留打印布局；PDF 转 Excel 提取 PDF 中的表格（每页一个工作表，扫描件无法提取）。",
            exts=(".xlsx", ".xls"),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(10)
        self.rb_x2p = QRadioButton("Excel → PDF")
        self.rb_p2x = QRadioButton("PDF → Excel")
        self.rb_x2p.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.rb_x2p)
        group.addButton(self.rb_p2x)
        self.rb_x2p.toggled.connect(self._on_mode_changed)
        row.addWidget(self.rb_x2p)
        row.addWidget(self.rb_p2x)
        row.addStretch(1)
        self.extra.addLayout(row)
        self._on_mode_changed()

        self._register_setting(self.rb_x2p, "mode")

    def _on_mode_changed(self):
        if self.rb_x2p.isChecked():
            self._set_exts((".xlsx", ".xls"))
        else:
            self._set_exts((".pdf",))

    def _build_task(self, files, out_dir):
        xlsx_to_pdf_mode = self.rb_x2p.isChecked()

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
                    if xlsx_to_pdf_mode:
                        out = self.output_path(f, ".pdf", out_dir)
                        xlsx_to_pdf(f, out, on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
                    else:
                        out = self.output_path(f, ".xlsx", out_dir)
                        pdf_to_xlsx(f, out, on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
                    ok += 1
                    on_log(f"✓ 完成：{out}")
                except CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    on_log(f"✗ 失败：{exc}")
                on_progress(int((i + 1) * 100 / total))
            if ok == total:
                return ok, total
            raise RuntimeError(f"完成：成功 {ok} / {total}，详见下方日志")

        return task
