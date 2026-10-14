"""ffmpeg 调用封装：二进制探测、时长探测、带进度回调的命令执行。

ffmpeg 查找顺序：
1. 项目 tools/ 目录下的便携版（随 PyInstaller 打包分发）
2. 系统 PATH（如 winget 安装的 Gyan.FFmpeg）
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

if getattr(sys, "frozen", False):  # PyInstaller 打包后：解包临时目录
    PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = PROJECT_ROOT / "tools"


class FFmpegNotFoundError(RuntimeError):
    """找不到 ffmpeg/ffprobe 可执行文件。"""


class FFmpegError(RuntimeError):
    """ffmpeg 执行失败。"""


class CancelledError(RuntimeError):
    """任务被用户取消。"""


def find_ffmpeg() -> str:
    local = TOOLS_DIR / "ffmpeg.exe"
    if local.exists():
        return str(local)
    path = shutil.which("ffmpeg")
    if path:
        return path
    raise FFmpegNotFoundError(
        "未找到 ffmpeg：请将 ffmpeg.exe 放入项目 tools 目录，"
        "或执行 winget install Gyan.FFmpeg 安装到系统"
    )


def find_ffprobe() -> str:
    local = TOOLS_DIR / "ffprobe.exe"
    if local.exists():
        return str(local)
    path = shutil.which("ffprobe")
    if path:
        return path
    raise FFmpegNotFoundError("未找到 ffprobe：请将 ffprobe.exe 放入项目 tools 目录")


def probe_duration(path) -> float | None:
    """探测媒体时长（秒）；失败返回 None。"""
    try:
        out = subprocess.run(
            [
                find_ffprobe(), "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if out.returncode == 0 and out.stdout.strip():
            return float(out.stdout.strip())
    except Exception:  # noqa: BLE001 - 探测失败不致命
        pass
    return None


def _parse_time(line: str) -> float | None:
    """从 -progress 输出行解析已处理时长（秒）。

    注意：ffmpeg 的 out_time_ms 实际单位也是微秒（历史遗留）。
    """
    for key in ("out_time_us=", "out_time_ms="):
        if line.startswith(key):
            try:
                return int(line[len(key):]) / 1_000_000.0
            except ValueError:
                return None
    return None


def run(cmd: list[str], on_progress, on_log, is_cancelled, duration: float | None = None):
    """执行 ffmpeg 命令。

    cmd 应包含 "-progress pipe:1 -nostats" 以输出可解析进度。
    duration 为输入时长（秒）；未知时 on_progress(None)（界面显示忙碌态）。
    失败抛出 FFmpegError，取消抛出 CancelledError。
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert proc.stdout is not None
    last_pct: float | None = None
    if not duration:
        on_progress(None)
    try:
        for line in proc.stdout:
            if is_cancelled():
                proc.kill()
                raise CancelledError("任务已取消")
            line = line.strip()
            if line.startswith("out_time"):
                t = _parse_time(line)
                if t is not None and duration:
                    pct = int(min(99, t / duration * 100))
                    if pct != last_pct:
                        last_pct = pct
                        on_progress(pct)
            elif line == "progress=end" and duration:
                on_progress(100)
    finally:
        proc.wait()
        stderr_tail: list[str] = []
        if proc.stderr is not None:
            err = proc.stderr.read()
            stderr_tail = [l for l in err.strip().splitlines() if l.strip()]
    if proc.returncode != 0:
        detail = "\n".join(stderr_tail[-6:]) or "未知错误"
        raise FFmpegError(f"ffmpeg 执行失败（exit {proc.returncode}）：\n{detail}")
