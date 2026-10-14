"""音频格式互转（基于 ffmpeg）。"""

from __future__ import annotations

from pathlib import Path

from app.core import ffmpeg as ff
from app.core.video import VIDEO_EXTS

# 支持输入的音频格式（含视频容器：视频文件也能直接提取音频转格式）
AUDIO_IN_EXTS = {
    ".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".wma", ".opus", ".amr", ".mka",
} | VIDEO_EXTS

OUTPUT_FORMATS = ("mp3", "wav", "aac", "m4a", "flac", "ogg")

# 输出格式 -> (编码器, 是否支持码率参数)
CODECS = {
    "mp3": ("libmp3lame", True),
    "wav": ("pcm_s16le", False),
    "aac": ("aac", True),
    "m4a": ("aac", True),
    "flac": ("flac", False),
    "ogg": ("libvorbis", True),
}

BITRATES = ("128k", "192k", "256k", "320k")


def convert_audio(src, out, fmt: str, bitrate: str = "192k",
                  on_progress=None, on_log=None, is_cancelled=None) -> None:
    """把任意音/视频文件的音轨转换为目标格式。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    codec, lossy = CODECS[fmt]
    args = ["-b:a", bitrate] if lossy else []
    cmd = [
        ff.find_ffmpeg(), "-y", "-i", str(src),
        "-vn", "-c:a", codec, *args,
        "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
        str(out),
    ]
    on_log(f"转换音频：{Path(src).name} → {Path(out).name}（{codec}）")
    ff.run(cmd, on_progress, on_log, is_cancelled, ff.probe_duration(src))
    on_progress(100)
