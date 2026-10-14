"""PDF 拆分功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSpinBox,
)

from app.core.pdf_split import split_pdf
from app.ui.base import ConverterPage
from app.workers import CancelledError


class PdfSplitPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "PDF 拆分",
            "把一个 PDF 拆成多个文件：每页一个文件、每 N 页一组，或按自定义页码范围（如 1-3,5,7-）导出。",
            exts=(".pdf",),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(10)
        self.rb_single = QRadioButton("每页一个文件")
        self.rb_every = QRadioButton("每 N 页一组")
        self.rb_ranges = QRadioButton("自定义页码范围")
        self.rb_single.setChecked(True)
        group = QButtonGroup(self)
        for rb in (self.rb_single, self.rb_every, self.rb_ranges):
            group.addButton(rb)
            row.addWidget(rb)
        self.spin_every = QSpinBox()
        self.spin_every.setRange(2, 500)
        self.spin_every.setValue(5)
        self.spin_every.setSuffix(" 页")
        self.edit_ranges = QLineEdit()
        self.edit_ranges.setPlaceholderText("如：1-3,5,7-")
        self.edit_ranges.setMaximumWidth(180)
        row.addWidget(self.spin_every)
        row.addWidget(self.edit_ranges)
        row.addStretch(1)
        self.extra.addLayout(row)

        self.rb_single.toggled.connect(self._on_mode_changed)
        self._on_mode_changed()

        self._register_setting(self.rb_single, "mode")
        self._register_setting(self.spin_every, "every")
        self._register_setting(self.edit_ranges, "ranges")

    def _on_mode_changed(self):
        self.spin_every.setVisible(self.rb_every.isChecked())
        self.edit_ranges.setVisible(self.rb_ranges.isChecked())

    def _build_task(self, files, out_dir):
        if self.rb_every.isChecked():
            mode, every, ranges = "every", self.spin_every.value(), ""
        elif self.rb_ranges.isChecked():
            mode, every, ranges = "ranges", 5, self.edit_ranges.text().strip()
        else:
            mode, every, ranges = "single", 5, ""

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
                    out_dir_i = out_dir or Path(f).parent
                    n = split_pdf(
                        f, out_dir_i, mode=mode, every=every, ranges=ranges,
                        on_progress=sub, on_log=on_log, is_cancelled=is_cancelled,
                    )
                    ok += 1
                    on_log(f"✓ 完成：拆分为 {n} 个文件 → {out_dir_i}")
                except CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    on_log(f"✗ 失败：{exc}")
                on_progress(int((i + 1) * 100 / total))
            if ok == total:
                return ok, total
            raise RuntimeError(f"完成：成功 {ok} / {total}，详见下方日志")

        return task
