"""PDF ⇄ 图片 功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QSpinBox,
)

from app.core.pdf_image import IMAGE_EXTS, images_to_pdf, pdf_to_images
from app.ui.base import ConverterPage
from app.workers import CancelledError


class PdfImagePage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "PDF ⇄ 图片",
            "PDF 逐页渲染为 PNG/JPG（可调清晰度）；或将多张图片按文件名排序合成一个 PDF。",
            exts=(".pdf",),
            parent=parent,
        )
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.rb_p2i = QRadioButton("PDF → 图片")
        self.rb_i2p = QRadioButton("图片 → PDF")
        self.rb_p2i.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.rb_p2i)
        group.addButton(self.rb_i2p)
        self.rb_p2i.toggled.connect(self._on_mode_changed)
        row1.addWidget(self.rb_p2i)
        row1.addWidget(self.rb_i2p)
        row1.addStretch(1)
        self.extra.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.lbl_fmt = QLabel("图片格式")
        self.cmb_fmt = QComboBox()
        self.cmb_fmt.addItems(["png", "jpg"])
        self.lbl_dpi = QLabel("清晰度")
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 600)
        self.spin_dpi.setValue(150)
        self.spin_dpi.setSuffix(" DPI")
        self.lbl_name = QLabel("输出文件名")
        self.edit_pdf_name = QLineEdit("合并图片.pdf")
        row2.addWidget(self.lbl_fmt)
        row2.addWidget(self.cmb_fmt)
        row2.addSpacing(10)
        row2.addWidget(self.lbl_dpi)
        row2.addWidget(self.spin_dpi)
        row2.addSpacing(10)
        row2.addWidget(self.lbl_name)
        row2.addWidget(self.edit_pdf_name, 1)
        self.extra.addLayout(row2)
        self._on_mode_changed()

        self._register_setting(self.rb_p2i, "mode")
        self._register_setting(self.cmb_fmt, "format")
        self._register_setting(self.spin_dpi, "dpi")
        self._register_setting(self.edit_pdf_name, "pdf_name")

    def _on_mode_changed(self):
        p2i = self.rb_p2i.isChecked()
        if p2i:
            self._set_exts((".pdf",))
        else:
            self._set_exts(tuple(sorted(IMAGE_EXTS)))
        for w in (self.lbl_fmt, self.cmb_fmt, self.lbl_dpi, self.spin_dpi):
            w.setVisible(p2i)
        for w in (self.lbl_name, self.edit_pdf_name):
            w.setVisible(not p2i)

    def _valid_input(self, files):
        if not super()._valid_input(files):
            return False
        if self.rb_i2p.isChecked():
            name = self.edit_pdf_name.text().strip()
            if not name.lower().endswith(".pdf"):
                QMessageBox.warning(self, "提示", "输出文件名必须以 .pdf 结尾")
                return False
        return True

    def _build_task(self, files, out_dir):
        p2i = self.rb_p2i.isChecked()
        fmt = self.cmb_fmt.currentText()
        dpi = self.spin_dpi.value()
        pdf_name = self.edit_pdf_name.text().strip()

        def task(on_progress, on_log, is_cancelled):
            if not p2i:
                out = (out_dir or Path(files[0]).parent) / pdf_name
                if out.resolve() in {Path(f).resolve() for f in files}:
                    raise RuntimeError("输出文件不能与输入图片同名，请修改输出文件名")
                n = images_to_pdf(files, out, on_progress=on_progress, on_log=on_log, is_cancelled=is_cancelled)
                on_log(f"✓ 完成：{n} 张图片已合成为 {out}")
                return n, n

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
                    out_dir_i = (out_dir or Path(f).parent) / f"{Path(f).stem}_images"
                    n = pdf_to_images(f, out_dir_i, fmt=fmt, dpi=dpi,
                                      on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
                    ok += 1
                    on_log(f"✓ 完成：{n} 张图片 → {out_dir_i}")
                except CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    on_log(f"✗ 失败：{exc}")
                on_progress(int((i + 1) * 100 / total))
            if ok == total:
                return ok, total
            raise RuntimeError(f"完成：成功 {ok} / {total}，详见下方日志")

        return task
