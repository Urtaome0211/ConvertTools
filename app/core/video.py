"""基于 ffmpeg 的视频/音频功能：格式转换、音频提取、视频提取、音视频合成。"""

from __future__ import annotations

from pathlib import Path

from app.core import ffmpeg as ff

# 支持输入的视频容器格式
VIDEO_EXTS = {
    ".avi", ".mp4", ".mkv", ".flv", ".mov", ".wmv", ".webm",
    ".m4v", ".ts", ".mpeg", ".mpg", ".3gp",
}

# 支持输出的视频格式
OUTPUT_FORMATS = ("mp4", "mkv", "avi", "flv")

# 提取音频支持的输出格式 -> (编码器, 附加参数)
AUDIO_CODECS = {
    "mp3": ("libmp3lame", ["-q:a", "2"]),
    "wav": ("pcm_s16le", []),
    "aac": ("aac", ["-b:a", "192k"]),
    "m4a": ("aac", ["-b:a", "192k"]),
}

# 画质档位 -> CRF（越小越清晰、体积越大）
CRF_MAP = {
    "高画质（文件大）": 18,
    "标准（推荐）": 23,
    "小体积（画质略低）": 28,
}


def convert_video(src, out, fmt: str, crf: int = 23,
                  on_progress=None, on_log=None, is_cancelled=None) -> None:
    """视频格式转换。

    编码策略：mp4/mkv/flv 用 H.264 + AAC；avi 用 MPEG-4 + MP3（兼容性最佳）。
    """
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    codec, acodec, ab = "libx264", "aac", "192k"
    if fmt == "avi":
        codec, acodec = "mpeg4", "libmp3lame"
    extra = ["-movflags", "+faststart"] if fmt == "mp4" else []

    cmd = [
        ff.find_ffmpeg(), "-y", "-i", str(src),
        "-c:v", codec, "-crf", str(crf), "-preset", "medium",
        "-c:a", acodec, "-b:a", ab,
        *extra,
        "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
        str(out),
    ]
    on_log(f"开始转码：{Path(src).name} → {Path(out).name}（{codec}）")
    ff.run(cmd, on_progress, on_log, is_cancelled, ff.probe_duration(src))
    on_progress(100)


def extract_audio(src, out, fmt: str,
                  on_progress=None, on_log=None, is_cancelled=None) -> None:
    """从视频中提取音频轨（分离）。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    codec, args = AUDIO_CODECS[fmt]
    cmd = [
        ff.find_ffmpeg(), "-y", "-i", str(src),
        "-vn", "-c:a", codec, *args,
        "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
        str(out),
    ]
    on_log(f"提取音频：{Path(src).name} → {Path(out).name}")
    ff.run(cmd, on_progress, on_log, is_cancelled, ff.probe_duration(src))
    on_progress(100)


def extract_video(src, out,
                  on_progress=None, on_log=None, is_cancelled=None) -> None:
    """提取视频轨（去音轨）。优先流复制；容器不兼容时回退重编码。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)
    duration = ff.probe_duration(src)

    cmd = [
        ff.find_ffmpeg(), "-y", "-i", str(src),
        "-an", "-c:v", "copy",
        "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
        str(out),
    ]
    on_log(f"提取视频轨（无音频）：{Path(src).name} → {Path(out).name}")
    try:
        ff.run(cmd, on_progress, on_log, is_cancelled, duration)
    except ff.FFmpegError:
        on_log("直接复制视频流失败（编码与容器不兼容），改用 H.264 重新编码 …")
        cmd2 = [
            ff.find_ffmpeg(), "-y", "-i", str(src),
            "-an", "-c:v", "libx264", "-crf", "23", "-preset", "medium",
            "-loglevel", "error",
            "-progress", "pipe:1", "-nostats",
            str(out),
        ]
        ff.run(cmd2, on_progress, on_log, is_cancelled, duration)
    on_progress(100)


def merge_av(video, audio, out,
             on_progress=None, on_log=None, is_cancelled=None) -> None:
    """把音频合并进视频（合成）：视频轨原样复制，音频轨转 AAC。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    cmd = [
        ff.find_ffmpeg(), "-y",
        "-i", str(video), "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-loglevel", "error",
        "-progress", "pipe:1", "-nostats",
        str(out),
    ]
    on_log(f"合成音视频：{Path(video).name} + {Path(audio).name} → {Path(out).name}")
    ff.run(cmd, on_progress, on_log, is_cancelled, ff.probe_duration(video))
    on_progress(100)
