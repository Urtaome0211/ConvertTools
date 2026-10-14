"""视频压缩 / 分辨率调整（基于 ffmpeg）。"""

from __future__ import annotations

from pathlib import Path

from app.core import ffmpeg as ff
from app.core.video import CRF_MAP, VIDEO_EXTS

SCALE_MODES = (
    "不缩放",
    "1080p（1920×1080）",
    "720p（1280×720）",
    "480p（854×480）",
    "自定义宽度",
)

PRESET_HEIGHTS = {
    "1080p（1920×1080）": 1080,
    "720p（1280×720）": 720,
    "480p（854×480）": 480,
}


def compress_video(src, out, crf: int = 23, scale_mode: str = "不缩放",
                   width: int = 0,
                   on_progress=None, on_log=None, is_cancelled=None) -> tuple[int, int]:
    """压缩视频为 H.264 + AAC 的 mp4，可调整分辨率，返回 (原字节数, 新字节数)。

    预设分辨率用 min(目标,原始) 防止小视频被放大；自定义宽度按用户指定强制缩放。
    """
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    vf = None
    if scale_mode == "自定义宽度":
        vf = f"scale={int(width)}:-2"
    elif scale_mode in PRESET_HEIGHTS:
        h = PRESET_HEIGHTS[scale_mode]
        vf = f"scale=-2:'min({h},ih)'"

    cmd = [ff.find_ffmpeg(), "-y", "-i", str(src)]
    if vf:
        cmd += ["-vf", vf]
    cmd += [
        "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
        str(out),
    ]
    scale_txt = f"，缩放 {scale_mode}" if vf else ""
    on_log(f"压缩视频：{Path(src).name} → {Path(out).name}（CRF {crf}{scale_txt}）")
    ff.run(cmd, on_progress, on_log, is_cancelled, ff.probe_duration(src))
    on_progress(100)
    return Path(src).stat().st_size, Path(out).stat().st_size
