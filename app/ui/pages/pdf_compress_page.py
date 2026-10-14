"""PDF 压缩功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSpinBox,
)

from app.core.pdf_compress import compress_pdf
from app.core.utils import human_size
from app.ui.base import ConverterPage
from app.workers import CancelledError


class PdfCompressPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "PDF 压缩",
            "无损模式清理冗余对象并压缩内部流；有损模式将页面重渲染为 JPEG（压缩率更高，文字会轻微模糊）。",
            exts=(".pdf",),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(10)
        self.rb_lossless = QRadioButton("无损压缩")
        self.rb_lossy = QRadioButton("有损压缩")
        self.rb_lossless.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.rb_lossless)
        group.addButton(self.rb_lossy)
        row.addWidget(self.rb_lossless)
        row.addWidget(self.rb_lossy)
        row.addSpacing(10)
        self.lbl_q = QLabel("JPEG 质量")
        self.spin_q = QSpinBox()
        self.spin_q.setRange(1, 100)
        self.spin_q.setValue(85)
        self.lbl_dpi = QLabel("清晰度")
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 300)
        self.spin_dpi.setValue(150)
        self.spin_dpi.setSuffix(" DPI")
        row.addWidget(self.lbl_q)
        row.addWidget(self.spin_q)
        row.addSpacing(10)
        row.addWidget(self.lbl_dpi)
        row.addWidget(self.spin_dpi)
        row.addStretch(1)
        self.extra.addLayout(row)

        self.rb_lossless.toggled.connect(self._on_mode_changed)
        self._on_mode_changed()

        self._register_setting(self.rb_lossless, "mode")
        self._register_setting(self.spin_q, "quality")
        self._register_setting(self.spin_dpi, "dpi")

    def _on_mode_changed(self):
        lossy = self.rb_lossy.isChecked()
        for w in (self.lbl_q, self.spin_q, self.lbl_dpi, self.spin_dpi):
            w.setVisible(lossy)

    def _build_task(self, files, out_dir):
        mode = "有损" if self.rb_lossy.isChecked() else "无损"
        quality = self.spin_q.value()
        dpi = self.spin_dpi.value()

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
                    out = self.output_path(f, "_压缩.pdf", out_dir)
                    in_size, out_size = compress_pdf(
                        f, out, mode=mode, quality=quality, dpi=dpi,
                        on_progress=sub, on_log=on_log, is_cancelled=is_cancelled,
                    )
                    ok += 1
                    pct = (1 - out_size / in_size) * 100 if in_size else 0
                    verb = "减小" if out_size <= in_size else "增大"
                    on_log(
                        f"✓ {Path(out).name}：{human_size(in_size)} → "
                        f"{human_size(out_size)}（{verb} {abs(pct):.1f}%）"
                    )
                except CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    on_log(f"✗ 失败：{exc}")
                on_progress(int((i + 1) * 100 / total))
            if ok == total:
                return ok, total
            raise RuntimeError(f"完成：成功 {ok} / {total}，详见下方日志")

        return task
