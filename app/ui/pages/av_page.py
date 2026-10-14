"""音视频分离 / 合并功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
)

from app.core.video import AUDIO_CODECS, VIDEO_EXTS, extract_audio, extract_video, merge_av
from app.ui.base import ConverterPage
from app.workers import CancelledError

AUDIO_FILTER = "音频文件 (*.mp3 *.wav *.aac *.m4a *.flac *.ogg *.wma);;所有文件 (*.*)"
VIDEO_FILTER = "视频文件 (*.mp4 *.mkv *.avi *.flv *.mov *.wmv *.webm *.m4v *.ts);;所有文件 (*.*)"


class AvPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "音视频分离 / 合并",
            "从视频中提取音频、提取无声视频轨，或将音频与视频重新合成（支持批量）。",
            exts=tuple(sorted(VIDEO_EXTS)),
            parent=parent,
        )
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.rb_audio = QRadioButton("提取音频")
        self.rb_video = QRadioButton("提取无声视频")
        self.rb_merge = QRadioButton("合并音频与视频")
        self.rb_audio.setChecked(True)
        group = QButtonGroup(self)
        for rb in (self.rb_audio, self.rb_video, self.rb_merge):
            group.addButton(rb)
            row1.addWidget(rb)
        row1.addStretch(1)
        self.extra.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.lbl_afmt = QLabel("音频格式")
        self.cmb_afmt = QComboBox()
        self.cmb_afmt.addItems(list(AUDIO_CODECS.keys()))
        self.lbl_container = QLabel("输出容器")
        self.cmb_container = QComboBox()
        self.cmb_container.addItems(["mp4", "mkv"])
        row2.addWidget(self.lbl_afmt)
        row2.addWidget(self.cmb_afmt)
        row2.addSpacing(10)
        row2.addWidget(self.lbl_container)
        row2.addWidget(self.cmb_container)
        row2.addStretch(1)
        self.extra.addLayout(row2)

        # 合并模式：两个文件选择行
        row3 = QHBoxLayout()
        row3.setSpacing(8)
        self.lbl_video_file = QLabel("视频文件")
        self.edit_video = QLineEdit()
        self.edit_video.setReadOnly(True)
        self.edit_video.setPlaceholderText("选择视频文件")
        self.btn_video = QPushButton("浏览…")
        self.btn_video.clicked.connect(self._pick_video)
        row3.addWidget(self.lbl_video_file)
        row3.addWidget(self.edit_video, 1)
        row3.addWidget(self.btn_video)
        self.extra.addLayout(row3)

        row4 = QHBoxLayout()
        row4.setSpacing(8)
        self.lbl_audio_file = QLabel("音频文件")
        self.edit_audio = QLineEdit()
        self.edit_audio.setReadOnly(True)
        self.edit_audio.setPlaceholderText("选择音频文件")
        self.btn_audio = QPushButton("浏览…")
        self.btn_audio.clicked.connect(self._pick_audio)
        row4.addWidget(self.lbl_audio_file)
        row4.addWidget(self.edit_audio, 1)
        row4.addWidget(self.btn_audio)
        self.extra.addLayout(row4)

        self.rb_audio.toggled.connect(self._on_mode_changed)
        self._on_mode_changed()

        self._register_setting(self.rb_audio, "mode")
        self._register_setting(self.cmb_afmt, "audio_format")
        self._register_setting(self.cmb_container, "container")
        self._register_setting(self.edit_video, "video_file")
        self._register_setting(self.edit_audio, "audio_file")

    def _default_out_dir(self, files):
        if self.rb_merge.isChecked() and self.edit_video.text().strip():
            return Path(self.edit_video.text().strip()).parent
        return super()._default_out_dir(files)

    def _on_mode_changed(self):
        merge = self.rb_merge.isChecked()
        self.drop_zone.setVisible(not merge)
        self.file_card.setVisible(not merge)
        for w in (self.lbl_video_file, self.edit_video, self.btn_video,
                  self.lbl_audio_file, self.edit_audio, self.btn_audio):
            w.setVisible(merge)
        for w in (self.lbl_afmt, self.cmb_afmt):
            w.setVisible(self.rb_audio.isChecked())
        for w in (self.lbl_container, self.cmb_container):
            w.setVisible(not self.rb_audio.isChecked())

    def _pick_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", VIDEO_FILTER)
        if path:
            self.edit_video.setText(path)

    def _pick_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", AUDIO_FILTER)
        if path:
            self.edit_audio.setText(path)

    def _valid_input(self, files):
        if self.rb_merge.isChecked():
            v, a = self.edit_video.text().strip(), self.edit_audio.text().strip()
            if not v or not Path(v).is_file():
                QMessageBox.warning(self, "提示", "请先选择视频文件")
                return False
            if not a or not Path(a).is_file():
                QMessageBox.warning(self, "提示", "请先选择音频文件")
                return False
            return True
        return super()._valid_input(files)

    def _build_task(self, files, out_dir):
        if self.rb_merge.isChecked():
            video = self.edit_video.text().strip()
            audio = self.edit_audio.text().strip()
            container = self.cmb_container.currentText()

            def task(on_progress, on_log, is_cancelled):
                out = self.output_path(video, f".{container}", out_dir)
                merge_av(video, audio, out, on_progress=on_progress, on_log=on_log, is_cancelled=is_cancelled)
                on_log(f"✓ 完成：{out}")
                return 1, 1

            return task

        extract_audio_mode = self.rb_audio.isChecked()
        afmt = self.cmb_afmt.currentText()
        container = self.cmb_container.currentText()

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
                    if extract_audio_mode:
                        out = self.output_path(f, f".{afmt}", out_dir)
                        extract_audio(f, out, afmt, on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
                    else:
                        out = self.output_path(f, f".{container}", out_dir)
                        extract_video(f, out, on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
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
