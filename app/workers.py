"""后台任务线程封装。

所有耗时转换都在子线程执行，避免卡死界面。
任务函数约定签名：task(on_progress, on_log, is_cancelled) -> (成功数, 总数) | None
"""

from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal


class CancelledError(RuntimeError):
    """用户主动取消任务。"""


class TaskWorker(QThread):
    """在子线程中运行一个转换任务。

    信号：
    - progress(object): int(0-100) 表示百分比；None 表示进度未知（忙碌态）
    - log(str): 追加日志
    - finished(bool, str): (是否全部成功, 结果消息)
    """

    progress = Signal(object)
    log = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self._task = task
        self._cancelled = False

    def run(self):  # noqa: D401 - 线程入口
        ok, msg = False, ""
        try:
            result = self._task(
                on_progress=self.progress.emit,
                on_log=self.log.emit,
                is_cancelled=lambda: self._cancelled,
            )
            if isinstance(result, tuple) and len(result) == 2:
                done, total = result
                ok, msg = True, f"完成：成功 {done} / {total}"
            else:
                ok, msg = True, "全部完成"
        except CancelledError:
            msg = "已取消"
        except Exception as exc:  # noqa: BLE001 - 需要把任何错误反馈给界面
            msg = str(exc) or exc.__class__.__name__
            self.log.emit(traceback.format_exc(limit=2))
        finally:
            self.finished.emit(ok, msg)

    def cancel(self):
        self._cancelled = True
