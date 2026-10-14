"""视频转 GIF 动图（palettegen + paletteuse 两遍调色板算法）。"""

from __future__ import annotations

from pathlib import Path

from app.core import ffmpeg as ff
from app.core.video import VIDEO_EXTS


def make_gif(src, out, fps: int = 10, width: int = 480,
             start: float = 0.0, end: float = 0.0,
             on_progress=None, on_log=None, is_cancelled=None) -> int:
    """把视频片段转成循环 GIF，返回 GIF 文件字节数。

    start/end 单位秒，0 表示从头 / 到尾；width<=0 表示使用原宽度。
    """
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    scale = f"scale={int(width)}:-1:flags=lanczos" if width > 0 else "scale=trunc(iw/2)*2:-2"
    vf = (
        f"fps={fps},{scale},split[s0][s1];"
        "[s0]palettegen=max_colors=256[p];"
        "[s1][p]paletteuse=dither=bayer"
    )
    cmd = [ff.find_ffmpeg(), "-y"]
    if start > 0:
        cmd += ["-ss", f"{start:.2f}"]
    cmd += ["-i", str(src)]
    if end > start:
        cmd += ["-t", f"{end - start:.2f}"]
    cmd += [
        "-vf", vf, "-loop", "0",
        "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
        str(out),
    ]
    seg = f"，片段 {start:.1f}s–{end:.1f}s" if end > start else ""
    on_log(f"生成 GIF：{Path(src).name} → {Path(out).name}（{fps} fps{seg}）")
    duration = ff.probe_duration(src)
    if duration:
        duration -= start if start > 0 else 0
        if end > start:
            duration = min(duration, end - start)
        duration = max(duration, 0.1)
    ff.run(cmd, on_progress, on_log, is_cancelled, duration)
    on_progress(100)
    return Path(out).stat().st_size
