"""音频格式互转功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel

from app.core.audio_convert import AUDIO_IN_EXTS, BITRATES, CODECS, OUTPUT_FORMATS, convert_audio
from app.ui.base import ConverterPage
from app.workers import CancelledError


class AudioPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "音频格式转换",
            "在 mp3 / wav / aac / m4a / flac / ogg 之间互转；也可以直接把视频文件的音轨转成目标格式。",
            exts=tuple(sorted(AUDIO_IN_EXTS)),
            parent=parent,
        )
        row = QHBoxLayout()
        row.setSpacing(8)
        self.lbl_fmt = QLabel("输出格式")
        self.cmb_fmt = QComboBox()
        self.cmb_fmt.addItems(list(OUTPUT_FORMATS))
        self.lbl_br = QLabel("码率")
        self.cmb_br = QComboBox()
        self.cmb_br.addItems(list(BITRATES))
        self.cmb_br.setCurrentText("192k")
        row.addWidget(self.lbl_fmt)
        row.addWidget(self.cmb_fmt)
        row.addSpacing(10)
        row.addWidget(self.lbl_br)
        row.addWidget(self.cmb_br)
        row.addStretch(1)
        self.extra.addLayout(row)

        self.cmb_fmt.currentTextChanged.connect(self._on_fmt_changed)
        self._on_fmt_changed()

        self._register_setting(self.cmb_fmt, "format")
        self._register_setting(self.cmb_br, "bitrate")

    def _on_fmt_changed(self):
        lossy = CODECS[self.cmb_fmt.currentText()][1]
        self.lbl_br.setVisible(lossy)
        self.cmb_br.setVisible(lossy)

    def _build_task(self, files, out_dir):
        fmt = self.cmb_fmt.currentText()
        bitrate = self.cmb_br.currentText()

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
                    convert_audio(f, out, fmt, bitrate=bitrate,
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
