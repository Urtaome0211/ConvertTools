"""PDF 加密 / 解密 / 水印功能页。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
)

from app.core.pdf_security import decrypt_pdf, encrypt_pdf, watermark_pdf
from app.ui.base import ConverterPage
from app.workers import CancelledError

IMAGE_FILTER = "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"


class PdfSecurityPage(ConverterPage):
    def __init__(self, parent=None):
        super().__init__(
            "PDF 加密 / 水印",
            "AES-256 口令加密、移除口令，或给每页居中添加文字 / 图片水印。",
            exts=(".pdf",),
            parent=parent,
        )
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.rb_encrypt = QRadioButton("加密")
        self.rb_decrypt = QRadioButton("解密")
        self.rb_watermark = QRadioButton("加水印")
        self.rb_encrypt.setChecked(True)
        group = QButtonGroup(self)
        for rb in (self.rb_encrypt, self.rb_decrypt, self.rb_watermark):
            group.addButton(rb)
            row1.addWidget(rb)
        row1.addStretch(1)
        self.extra.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.lbl_pwd = QLabel("密码")
        self.edit_pwd = QLineEdit()
        self.edit_pwd.setEchoMode(QLineEdit.Password)
        self.edit_pwd.setPlaceholderText("输入 PDF 口令")
        self.edit_pwd.setMaximumWidth(280)
        row2.addWidget(self.lbl_pwd)
        row2.addWidget(self.edit_pwd)
        row2.addStretch(1)
        self.extra.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(10)
        self.rb_wm_text = QRadioButton("文字水印")
        self.rb_wm_image = QRadioButton("图片水印")
        self.rb_wm_text.setChecked(True)
        wm_group = QButtonGroup(self)
        wm_group.addButton(self.rb_wm_text)
        wm_group.addButton(self.rb_wm_image)
        row3.addWidget(self.rb_wm_text)
        row3.addWidget(self.rb_wm_image)
        row3.addStretch(1)
        self.extra.addLayout(row3)

        row4 = QHBoxLayout()
        row4.setSpacing(8)
        self.edit_wm_text = QLineEdit("内部资料 请勿外传")
        self.edit_wm_text.setMaximumWidth(360)
        self.edit_wm_image = QLineEdit()
        self.edit_wm_image.setReadOnly(True)
        self.edit_wm_image.setPlaceholderText("选择水印图片")
        self.btn_wm_image = QPushButton("浏览…")
        self.btn_wm_image.clicked.connect(self._pick_image)
        row4.addWidget(self.edit_wm_text, 1)
        row4.addWidget(self.edit_wm_image, 1)
        row4.addWidget(self.btn_wm_image)
        self.extra.addLayout(row4)

        row5 = QHBoxLayout()
        row5.setSpacing(8)
        self.lbl_fs = QLabel("字号")
        self.spin_fs = QSpinBox()
        self.spin_fs.setRange(12, 200)
        self.spin_fs.setValue(48)
        self.lbl_op = QLabel("透明度")
        self.spin_op = QSpinBox()
        self.spin_op.setRange(5, 100)
        self.spin_op.setValue(15)
        self.spin_op.setSuffix(" %")
        self.lbl_ang = QLabel("角度")
        self.spin_ang = QSpinBox()
        self.spin_ang.setRange(0, 90)
        self.spin_ang.setValue(45)
        self.spin_ang.setSuffix(" °")
        row5.addWidget(self.lbl_fs)
        row5.addWidget(self.spin_fs)
        row5.addSpacing(10)
        row5.addWidget(self.lbl_op)
        row5.addWidget(self.spin_op)
        row5.addSpacing(10)
        row5.addWidget(self.lbl_ang)
        row5.addWidget(self.spin_ang)
        row5.addStretch(1)
        self.extra.addLayout(row5)

        self.rb_encrypt.toggled.connect(self._on_mode_changed)
        self.rb_wm_text.toggled.connect(self._on_wm_mode_changed)
        self._on_mode_changed()

        self._register_setting(self.rb_encrypt, "mode")
        self._register_setting(self.edit_pwd, "password")
        self._register_setting(self.rb_wm_text, "wm_type")
        self._register_setting(self.edit_wm_text, "wm_text")
        self._register_setting(self.edit_wm_image, "wm_image")
        self._register_setting(self.spin_fs, "font_size")
        self._register_setting(self.spin_op, "opacity")
        self._register_setting(self.spin_ang, "angle")

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择水印图片", "", IMAGE_FILTER)
        if path:
            self.edit_wm_image.setText(path)

    def _on_mode_changed(self):
        watermark = self.rb_watermark.isChecked()
        for w in (self.lbl_pwd, self.edit_pwd):
            w.setVisible(not watermark)
        for w in (self.rb_wm_text, self.rb_wm_image, self.edit_wm_text,
                  self.edit_wm_image, self.btn_wm_image, self.lbl_fs,
                  self.spin_fs, self.lbl_op, self.spin_op, self.lbl_ang,
                  self.spin_ang):
            w.setVisible(watermark)
        self._on_wm_mode_changed()

    def _on_wm_mode_changed(self):
        if not self.rb_watermark.isChecked():
            return
        text = self.rb_wm_text.isChecked()
        self.edit_wm_text.setVisible(text)
        for w in (self.edit_wm_image, self.btn_wm_image, self.lbl_fs, self.spin_fs,
                  self.lbl_ang, self.spin_ang):
            w.setVisible(text)

    def _valid_input(self, files):
        if not super()._valid_input(files):
            return False
        if self.rb_watermark.isChecked():
            if self.rb_wm_text.isChecked() and not self.edit_wm_text.text().strip():
                QMessageBox.warning(self, "提示", "请填写水印文字")
                return False
            if self.rb_wm_image.isChecked() and not Path(self.edit_wm_image.text().strip()).is_file():
                QMessageBox.warning(self, "提示", "请选择水印图片文件")
                return False
        elif not self.edit_pwd.text():
            QMessageBox.warning(self, "提示", "请输入密码")
            return False
        return True

    def _build_task(self, files, out_dir):
        encrypt = self.rb_encrypt.isChecked()
        watermark = self.rb_watermark.isChecked()
        password = self.edit_pwd.text()
        wm_text = self.edit_wm_text.text().strip()
        wm_image = self.edit_wm_image.text().strip()
        font_size = self.spin_fs.value()
        opacity = self.spin_op.value() / 100
        angle = self.spin_ang.value()

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
                    if watermark:
                        out = self.output_path(f, "_水印.pdf", out_dir)
                        watermark_pdf(
                            f, out, text=wm_text, image_path=wm_image,
                            font_size=font_size, opacity=opacity, angle=angle,
                            on_progress=sub, on_log=on_log, is_cancelled=is_cancelled,
                        )
                    elif encrypt:
                        out = self.output_path(f, "_加密.pdf", out_dir)
                        encrypt_pdf(f, out, password,
                                    on_progress=sub, on_log=on_log, is_cancelled=is_cancelled)
                    else:
                        out = self.output_path(f, "_解密.pdf", out_dir)
                        decrypt_pdf(f, out, password,
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
