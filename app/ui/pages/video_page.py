"""视频格式转换功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel

from app.core.video import CRF_MAP, OUTPUT_FORMATS, VIDEO_EXTS, convert_video
from app.ui.base import ConverterPage
from app.workers import CancelledError


class VideoPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "视频格式转换",
            "批量转换视频容器格式：mp4 / mkv / flv 采用 H.264 + AAC，avi 采用 MPEG-4 + MP3（兼容性最佳）。",
            exts=tuple(sorted(VIDEO_EXTS)),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(8)
        self.lbl_fmt = QLabel("输出格式")
        self.cmb_fmt = QComboBox()
        self.cmb_fmt.addItems(list(OUTPUT_FORMATS))
        self.lbl_q = QLabel("画质")
        self.cmb_q = QComboBox()
        self.cmb_q.addItems(list(CRF_MAP.keys()))
        self.cmb_q.setCurrentText("标准（推荐）")
        row.addWidget(self.lbl_fmt)
        row.addWidget(self.cmb_fmt)
        row.addSpacing(10)
        row.addWidget(self.lbl_q)
        row.addWidget(self.cmb_q)
        row.addStretch(1)
        self.extra.addLayout(row)

        self._register_setting(self.cmb_fmt, "format")
        self._register_setting(self.cmb_q, "quality")

    def _build_task(self, files, out_dir):
        fmt = self.cmb_fmt.currentText()
        crf = CRF_MAP[self.cmb_q.currentText()]

        def task(on_progress, on_log, is_cancelled):
            total = len(files)
            ok = 0
            for i, f in enumerate(files):
                if is_cancelled():
                    raise CancelledError("任务已取消")
                on_log(f"[{i + 1}/{total}] {Path(f).name}")
                if Path(f).suffix.lower() == f".{fmt}":
                    on_log("  · 已是目标格式，跳过")
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
                    convert_video(f, out, fmt, crf=crf,
                                  on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
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
