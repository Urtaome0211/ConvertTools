"""视频压缩 / 分辨率调整功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSpinBox

from app.core.utils import human_size
from app.core.video import CRF_MAP, VIDEO_EXTS
from app.core.video_compress import SCALE_MODES, compress_video
from app.ui.base import ConverterPage
from app.workers import CancelledError


class VideoCompressPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "视频压缩",
            "H.264 + AAC 重新编码压缩为 mp4，可限制分辨率（预设档位不会放大小视频）。",
            exts=tuple(sorted(VIDEO_EXTS)),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(8)
        self.lbl_q = QLabel("画质")
        self.cmb_q = QComboBox()
        self.cmb_q.addItems(list(CRF_MAP.keys()))
        self.cmb_q.setCurrentText("标准（推荐）")
        self.lbl_scale = QLabel("分辨率")
        self.cmb_scale = QComboBox()
        self.cmb_scale.addItems(list(SCALE_MODES))
        self.lbl_w = QLabel("宽度")
        self.spin_w = QSpinBox()
        self.spin_w.setRange(16, 7680)
        self.spin_w.setValue(1280)
        self.spin_w.setSuffix(" px")
        row.addWidget(self.lbl_q)
        row.addWidget(self.cmb_q)
        row.addSpacing(10)
        row.addWidget(self.lbl_scale)
        row.addWidget(self.cmb_scale)
        row.addSpacing(10)
        row.addWidget(self.lbl_w)
        row.addWidget(self.spin_w)
        row.addStretch(1)
        self.extra.addLayout(row)

        self.cmb_scale.currentTextChanged.connect(self._on_scale_changed)
        self._on_scale_changed()

        self._register_setting(self.cmb_q, "quality")
        self._register_setting(self.cmb_scale, "scale_mode")
        self._register_setting(self.spin_w, "width")

    def _on_scale_changed(self):
        custom = self.cmb_scale.currentText() == "自定义宽度"
        self.lbl_w.setVisible(custom)
        self.spin_w.setVisible(custom)

    def _build_task(self, files, out_dir):
        crf = CRF_MAP[self.cmb_q.currentText()]
        scale_mode = self.cmb_scale.currentText()
        width = self.spin_w.value()

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
                    out = self.output_path(f, "_压缩.mp4", out_dir)
                    in_size, out_size = compress_video(
                        f, out, crf=crf, scale_mode=scale_mode, width=width,
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
