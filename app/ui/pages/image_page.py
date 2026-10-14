"""图片格式互转与压缩功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSpinBox

from app.core.image_convert import LOSSLESS_FORMATS, OUTPUT_FORMATS, RESIZE_MODES, convert_image
from app.core.pdf_image import IMAGE_EXTS
from app.core.utils import human_size
from app.ui.base import ConverterPage
from app.workers import CancelledError

SIZE_LABELS = {
    "不缩放": "",
    "按宽度": "目标宽度",
    "按高度": "目标高度",
    "长边限制": "最长边",
    "按百分比": "缩放比例",
}


class ImagePage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "图片格式转换",
            "在 jpg / png / webp / bmp / tiff 之间互转，支持等比例缩放与压缩质量调节。",
            exts=tuple(sorted(IMAGE_EXTS)),
            parent=parent,
        )
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.lbl_fmt = QLabel("输出格式")
        self.cmb_fmt = QComboBox()
        self.cmb_fmt.addItems(list(OUTPUT_FORMATS))
        self.lbl_q = QLabel("质量")
        self.spin_q = QSpinBox()
        self.spin_q.setRange(1, 100)
        self.spin_q.setValue(90)
        self.spin_q.setSuffix(" %")
        row1.addWidget(self.lbl_fmt)
        row1.addWidget(self.cmb_fmt)
        row1.addSpacing(10)
        row1.addWidget(self.lbl_q)
        row1.addWidget(self.spin_q)
        row1.addStretch(1)
        self.extra.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.lbl_resize = QLabel("缩放")
        self.cmb_resize = QComboBox()
        self.cmb_resize.addItems(list(RESIZE_MODES))
        self.lbl_val = QLabel("目标宽度")
        self.spin_val = QSpinBox()
        self.spin_val.setRange(1, 9999)
        self.spin_val.setValue(1080)
        self.spin_val.setSuffix(" px")
        row2.addWidget(self.lbl_resize)
        row2.addWidget(self.cmb_resize)
        row2.addSpacing(10)
        row2.addWidget(self.lbl_val)
        row2.addWidget(self.spin_val)
        row2.addStretch(1)
        self.extra.addLayout(row2)

        self.cmb_fmt.currentTextChanged.connect(self._on_fmt_changed)
        self.cmb_resize.currentTextChanged.connect(self._on_resize_changed)
        self._on_fmt_changed()
        self._on_resize_changed()

        self._register_setting(self.cmb_fmt, "format")
        self._register_setting(self.spin_q, "quality")
        self._register_setting(self.cmb_resize, "resize_mode")
        self._register_setting(self.spin_val, "resize_value")

    def _on_fmt_changed(self):
        lossy = self.cmb_fmt.currentText() not in LOSSLESS_FORMATS
        self.lbl_q.setVisible(lossy)
        self.spin_q.setVisible(lossy)

    def _on_resize_changed(self):
        mode = self.cmb_resize.currentText()
        label = SIZE_LABELS.get(mode, "")
        self.lbl_val.setVisible(bool(label))
        self.spin_val.setVisible(bool(label))
        self.lbl_val.setText(label)
        self.spin_val.setSuffix(" %" if mode == "按百分比" else " px")

    def _build_task(self, files, out_dir):
        fmt = self.cmb_fmt.currentText()
        quality = self.spin_q.value()
        resize_mode = self.cmb_resize.currentText()
        resize_value = self.spin_val.value()

        def task(on_progress, on_log, is_cancelled):
            total = len(files)
            ok = 0
            for i, f in enumerate(files):
                if is_cancelled():
                    raise CancelledError("任务已取消")
                on_log(f"[{i + 1}/{total}] {Path(f).name}")
                if Path(f).suffix.lower() == f".{fmt}" and resize_mode == "不缩放":
                    on_log("  · 已是目标格式且未缩放，跳过")
                    ok += 1
                    on_progress(int((i + 1) * 100 / total))
                    continue

                def sub(p, _i=i):
                    if p is None:
                        on_progress(None)
                    else:
                        on_progress(int((_i * 100 + p) / total))

                try:
                    out = self.output_path(f, f".{fmt}", out_dir)
                    in_size, out_size = convert_image(
                        f, out, fmt=fmt, quality=quality,
                        resize_mode=resize_mode, resize_value=resize_value,
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
