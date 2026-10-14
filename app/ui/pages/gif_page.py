"""视频转 GIF 功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
)

from app.core.gif_make import make_gif
from app.core.utils import human_size
from app.core.video import VIDEO_EXTS
from app.ui.base import ConverterPage
from app.workers import CancelledError


class GifPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "视频转 GIF",
            "把视频（或其中一段）转成循环播放的 GIF 动图，采用两遍调色板算法，色彩还原更好。",
            exts=tuple(sorted(VIDEO_EXTS)),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(8)
        self.lbl_fps = QLabel("帧率")
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(1, 30)
        self.spin_fps.setValue(10)
        self.spin_fps.setSuffix(" fps")
        self.lbl_w = QLabel("宽度")
        self.spin_w = QSpinBox()
        self.spin_w.setRange(0, 1920)
        self.spin_w.setValue(480)
        self.spin_w.setSuffix(" px")
        self.lbl_start = QLabel("起始")
        self.spin_start = QDoubleSpinBox()
        self.spin_start.setRange(0, 36000)
        self.spin_start.setDecimals(1)
        self.spin_start.setSuffix(" s")
        self.lbl_end = QLabel("结束")
        self.spin_end = QDoubleSpinBox()
        self.spin_end.setRange(0, 36000)
        self.spin_end.setDecimals(1)
        self.spin_end.setSuffix(" s")
        self.spin_end.setSpecialValueText("到结尾")
        row.addWidget(self.lbl_fps)
        row.addWidget(self.spin_fps)
        row.addSpacing(10)
        row.addWidget(self.lbl_w)
        row.addWidget(self.spin_w)
        row.addSpacing(10)
        row.addWidget(self.lbl_start)
        row.addWidget(self.spin_start)
        row.addSpacing(10)
        row.addWidget(self.lbl_end)
        row.addWidget(self.spin_end)
        row.addStretch(1)
        self.extra.addLayout(row)
        hint = QLabel("提示：宽度 0 表示保持原宽度；结束 0 表示一直转到视频结尾。")
        hint.setObjectName("hint")
        self.extra.addWidget(hint)

        self._register_setting(self.spin_fps, "fps")
        self._register_setting(self.spin_w, "width")
        self._register_setting(self.spin_start, "start")
        self._register_setting(self.spin_end, "end")

    def _valid_input(self, files):
        if not super()._valid_input(files):
            return False
        if 0 < self.spin_end.value() <= self.spin_start.value():
            QMessageBox.warning(self, "提示", "结束时间必须大于起始时间")
            return False
        return True

    def _build_task(self, files, out_dir):
        fps = self.spin_fps.value()
        width = self.spin_w.value()
        start = self.spin_start.value()
        end = self.spin_end.value()

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
                    out = self.output_path(f, ".gif", out_dir)
                    size = make_gif(f, out, fps=fps, width=width, start=start, end=end,
                                    on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
                    ok += 1
                    on_log(f"✓ 完成：{Path(out).name}（{human_size(size)}）")
                except CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    on_log(f"✗ 失败：{exc}")
                on_progress(int((i + 1) * 100 / total))
            if ok == total:
                return ok, total
            raise RuntimeError(f"完成：成功 {ok} / {total}，详见下方日志")

        return task
