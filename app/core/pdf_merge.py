"""多 PDF 合并。"""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz

from app.workers import CancelledError


def merge_pdfs(paths, out: Path,
               on_progress=None, on_log=None, is_cancelled=None) -> int:
    """按给定顺序把多个 PDF 合并为一个，返回文件数。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    total = len(paths)
    merged = fitz.open()
    try:
        for i, p in enumerate(paths, 1):
            if is_cancelled():
                raise CancelledError("任务已取消")
            on_log(f"合并中（{i}/{total}）：{Path(p).name}")
            with fitz.open(p) as doc:
                merged.insert_pdf(doc)
            on_progress(int(i / total * 100))
        merged.save(str(out), garbage=3, deflate=True)
    finally:
        merged.close()
    return total
