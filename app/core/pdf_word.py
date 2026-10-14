"""PDF ⇄ Word 转换。

- PDF → Word：pdf2docx（纯 Python，解析版面还原文字/表格）
- Word → PDF：见 app.core.office（调用本机 MS Word，保真度最高）
"""

from __future__ import annotations

from pathlib import Path

from pdf2docx import Converter

from app.workers import CancelledError


def pdf_to_docx(pdf, out, on_progress=None, on_log=None, is_cancelled=None) -> None:
    """PDF → Word (.docx)，支持文字、表格、图片的版面还原。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    on_log(f"解析版面中：{Path(pdf).name}（复杂文档可能需要几分钟）…")
    on_progress(None)  # pdf2docx 不提供逐页进度
    cv = Converter(str(pdf))
    try:
        if is_cancelled():
            raise CancelledError("任务已取消")
        cv.convert(str(out))
    finally:
        cv.close()
    on_progress(100)
