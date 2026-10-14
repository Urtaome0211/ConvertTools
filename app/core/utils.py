"""通用小工具。"""

from __future__ import annotations


def human_size(n: int | float) -> str:
    """把字节数格式化为人类可读文本（B / KB / MB / GB）。"""
    n = float(n)
    if n < 1024:
        return f"{int(n)} B"
    n /= 1024
    if n < 1024:
        return f"{n:.1f} KB"
    n /= 1024
    if n < 1024:
        return f"{n:.1f} MB"
    return f"{n / 1024:.2f} GB"
