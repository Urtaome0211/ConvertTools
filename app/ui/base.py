"""功能页基类：统一的拖放、文件列表、输出目录、进度条与日志区。

子类只需要：
1. 在 extra 布局里加入自己的参数控件
2. 实现 _valid_input(files) 与 _build_task(files, out_dir)
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTime, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets import DropZone
from app.workers import TaskWorker


class ConverterPage(QWidget):
    """转换功能页的公共骨架。"""

    def __init__(self, title: str, subtitle: str, exts=(), multi=True, parent=None,
                 settings_key: str = ""):
        super().__init__(parent)
        self.exts = tuple(e.lower() for e in exts)
        self.multi = multi
        self._worker: TaskWorker | None = None
        self._settings_key = settings_key or title
        self._last_out_dir: Path | None = None
        self._build_ui(title, subtitle)

    # ------------------------------------------------------------------ UI

    def _build_ui(self, title: str, subtitle: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        header = QLabel(title)
        header.setObjectName("pageTitle")
        root.addWidget(header)
        sub = QLabel(subtitle)
        sub.setObjectName("pageSub")
        root.addWidget(sub)

        # 拖放区
        self.drop_zone = DropZone(self.exts, self.multi)
        self.drop_zone.files_dropped.connect(self.add_files)
        root.addWidget(self.drop_zone)

        # 文件列表卡片
        self.file_card = QFrame()
        self.file_card.setObjectName("card")
        card_lay = QVBoxLayout(self.file_card)
        card_lay.setContentsMargins(12, 10, 12, 12)
        card_lay.setSpacing(8)
        list_header = QHBoxLayout()
        list_header.addWidget(QLabel("文件列表"))
        list_header.addStretch(1)
        self.btn_remove = QPushButton("移除选中")
        self.btn_remove.clicked.connect(self._remove_selected)
        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self._clear)
        list_header.addWidget(self.btn_remove)
        list_header.addWidget(self.btn_clear)
        card_lay.addLayout(list_header)

        self.file_list = QListWidget()
        self.file_list.setObjectName("files")
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setMaximumHeight(140)
        card_lay.addWidget(self.file_list)
        root.addWidget(self.file_card)

        # 附加参数区（子类按行填充：self.extra.addLayout(row)）
        self.extra = QVBoxLayout()
        self.extra.setSpacing(8)
        root.addLayout(self.extra)

        # 输出目录
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.chk_custom_dir = QCheckBox("自定义输出目录")
        self.chk_custom_dir.toggled.connect(self._toggle_outdir)
        self.edit_outdir = QLineEdit()
        self.edit_outdir.setEnabled(False)
        self.edit_outdir.setPlaceholderText("默认为与源文件相同的目录")
        self.btn_outdir = QPushButton("浏览…")
        self.btn_outdir.setEnabled(False)
        self.btn_outdir.clicked.connect(self._choose_outdir)
        out_row.addWidget(self.chk_custom_dir)
        out_row.addWidget(self.edit_outdir, 1)
        out_row.addWidget(self.btn_outdir)
        root.addLayout(out_row)

        # 开始 / 取消 / 进度
        act_row = QHBoxLayout()
        act_row.setSpacing(10)
        self.btn_start = QPushButton("开始转换")
        self.btn_start.setObjectName("primary")
        self.btn_start.clicked.connect(self.start)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel)
        act_row.addWidget(self.btn_start)
        act_row.addWidget(self.btn_cancel)
        act_row.addStretch(1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(240)
        self.progress.setVisible(False)
        act_row.addWidget(self.progress)
        root.addLayout(act_row)

        # 日志区
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("log")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        root.addWidget(self.log_view, 1)

    # -------------------------------------------------------------- 文件列表

    def _set_exts(self, exts):
        """切换页面模式时更新可接受的文件格式。"""
        self.exts = tuple(e.lower() for e in exts)
        self.drop_zone.set_exts(self.exts)

    def add_files(self, paths):
        """添加文件（或文件夹：递归收集其中匹配格式的文件）。"""
        candidates: list[Path] = []
        for raw in paths:
            p = Path(raw)
            if p.is_dir():
                candidates.extend(
                    f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in self.exts
                )
            elif p.is_file():
                candidates.append(p)

        existing = {
            self.file_list.item(i).data(Qt.UserRole)
            for i in range(self.file_list.count())
        }
        added = 0
        for p in candidates:
            key = str(p.resolve())
            if key in existing:
                continue
            if p.suffix.lower() not in self.exts:
                continue
            item = QListWidgetItem(p.name)
            item.setData(Qt.UserRole, key)
            item.setToolTip(key)
            self.file_list.addItem(item)
            existing.add(key)
            added += 1
        if not self.multi:
            while self.file_list.count() > 1:
                self.file_list.takeItem(0)
        if added:
            self._log(f"已添加 {added} 个文件")

    def _current_files(self) -> list[str]:
        return [
            self.file_list.item(i).data(Qt.UserRole)
            for i in range(self.file_list.count())
        ]

    def _remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def _clear(self):
        self.file_list.clear()

    # -------------------------------------------------------------- 输出目录

    def _toggle_outdir(self, checked: bool):
        self.edit_outdir.setEnabled(checked)
        self.btn_outdir.setEnabled(checked)

    def _choose_outdir(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出目录", self.edit_outdir.text())
        if d:
            self.edit_outdir.setText(d)

    def _custom_outdir(self) -> Path | None:
        if self.chk_custom_dir.isChecked() and self.edit_outdir.text().strip():
            d = Path(self.edit_outdir.text().strip())
            d.mkdir(parents=True, exist_ok=True)
            return d
        return None

    def output_path(self, src, new_ext: str, out_dir: Path | None = None) -> Path:
        """由源文件路径推导输出路径（自定义目录或同目录）。"""
        src = Path(src)
        out_dir = out_dir or src.parent
        out = out_dir / (src.stem + new_ext)
        if out.resolve() == src.resolve():
            raise ValueError(
                f"输出路径与输入文件相同，请更换输出目录：{src.name}"
            )
        return out

    # ------------------------------------------------------------------ 日志

    def _log(self, msg: str):
        ts = QTime.currentTime().toString("HH:mm:ss")
        self.log_view.appendPlainText(f"[{ts}] {msg}")

    # -------------------------------------------------------------- 任务执行

    def start(self):
        if self._worker is not None and self._worker.isRunning():
            return
        files = self._current_files()
        if not self._valid_input(files):
            return
        out_dir = self._custom_outdir()
        self._last_out_dir = out_dir or self._default_out_dir(files)
        task = self._build_task(files, out_dir)
        if task is None:
            return

        self._set_running(True)
        self._worker = TaskWorker(task, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._on_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _cancel(self):
        if self._worker is not None and self._worker.isRunning():
            self._log("正在取消任务 …")
            self._worker.cancel()

    def _set_running(self, running: bool):
        self.btn_start.setEnabled(not running)
        self.btn_cancel.setEnabled(running)
        self.drop_zone.setEnabled(not running)
        self.file_list.setEnabled(not running)
        self.progress.setVisible(running)
        if running:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)

    def _on_progress(self, p):
        if p is None:
            self.progress.setRange(0, 0)  # 忙碌态
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(int(p))

    def _on_log(self, msg: str):
        self._log(msg)

    def _on_finished(self, ok: bool, msg: str):
        self._set_running(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if ok else 0)
        if not msg or msg == "已取消":
            return
        QApplication.beep()
        if ok:
            settings = QSettings()
            if settings.value("behavior/no_success_popup", False, type=bool):
                return
            box = QMessageBox(self)
            box.setWindowTitle("转换完成")
            box.setIcon(QMessageBox.Information)
            box.setText(msg)
            chk = QCheckBox("不再弹出成功提示（保留提示音）")
            box.setCheckBox(chk)
            open_btn = box.addButton("打开输出文件夹", QMessageBox.ActionRole)
            box.addButton("关闭", QMessageBox.RejectRole)
            box.exec()
            if chk.isChecked():
                settings.setValue("behavior/no_success_popup", True)
            if box.clickedButton() is open_btn and self._last_out_dir:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_out_dir)))
        else:
            box = QMessageBox(self)
            box.setWindowTitle("提示")
            box.setIcon(QMessageBox.Warning)
            box.setText(msg)
            box.exec()

    # ------------------------------------------------------------ 参数记忆

    def _register_setting(self, widget, name: str):
        """注册需要记住的参数控件：启动时恢复上次的值，变更时自动保存。

        支持 QLineEdit / QCheckBox / QRadioButton / QComboBox / QSpinBox / QDoubleSpinBox。
        """
        w = widget
        key = f"{self._settings_key}/{name}"
        settings = QSettings()

        if settings.contains(key):
            v = settings.value(key)
            if isinstance(w, QLineEdit):
                w.setText(str(v))
            elif isinstance(w, (QCheckBox, QRadioButton)):
                w.setChecked(bool(v))
            elif isinstance(w, QComboBox):
                idx = w.findText(str(v))
                if idx >= 0:
                    w.setCurrentIndex(idx)
            elif isinstance(w, QSpinBox):
                w.setValue(int(v))
            elif isinstance(w, QDoubleSpinBox):
                w.setValue(float(v))

        def save():
            if isinstance(w, QLineEdit):
                QSettings().setValue(key, w.text())
            elif isinstance(w, (QCheckBox, QRadioButton)):
                QSettings().setValue(key, w.isChecked())
            elif isinstance(w, QComboBox):
                QSettings().setValue(key, w.currentText())
            elif isinstance(w, QSpinBox):
                QSettings().setValue(key, w.value())
            elif isinstance(w, QDoubleSpinBox):
                QSettings().setValue(key, w.value())

        if isinstance(w, QLineEdit):
            w.textChanged.connect(lambda *_: save())
        elif isinstance(w, (QCheckBox, QRadioButton)):
            w.toggled.connect(lambda *_: save())
        elif isinstance(w, QComboBox):
            w.currentTextChanged.connect(lambda *_: save())
        elif isinstance(w, (QSpinBox, QDoubleSpinBox)):
            w.valueChanged.connect(lambda *_: save())

    # ------------------------------------------------------------ 子类接口

    def _default_out_dir(self, files: list[str]) -> Path | None:
        """默认输出目录（用于完成弹窗的“打开输出文件夹”按钮）。"""
        return Path(files[0]).parent if files else None

    def _valid_input(self, files: list[str]) -> bool:
        """校验输入，不通过时需自行弹窗提示并返回 False。"""
        if not files:
            QMessageBox.warning(self, "提示", "请先添加要处理的文件")
            return False
        return True

    def _build_task(self, files: list[str], out_dir: Path | None):
        """返回任务函数 task(on_progress, on_log, is_cancelled)。

        任务内约定：全部成功返回 (成功数, 总数)；部分失败抛 RuntimeError。
        """
        raise NotImplementedError
