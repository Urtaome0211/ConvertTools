"""PDF 压缩：无损优化 + 有损重渲染（逐页转 JPEG 后重组成 PDF）。"""

from __future__ import annotations

import io
from pathlib import Path

import pymupdf as fitz
from PIL import Image

from app.workers import CancelledError


def compress_pdf(src, out, mode: str = "无损", quality: int = 85, dpi: int = 150,
                 on_progress=None, on_log=None, is_cancelled=None) -> tuple[int, int]:
    """压缩单个 PDF，返回 (原始字节数, 压缩后字节数)。

    mode: "无损" 清理冗余对象/压缩流；"有损" 按 DPI 渲染为 JPEG 再重组成 PDF。
    """
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    src_path = Path(src)
    in_size = src_path.stat().st_size
    doc = fitz.open(src_path)
    total = len(doc)
    try:
        if mode == "无损":
            on_log(f"无损优化：{src_path.name}")
            doc.save(str(out), garbage=3, deflate=True, clean=True)
        else:
            on_log(f"有损压缩（{dpi} DPI，JPEG 质量 {quality}）：{src_path.name}")
            new_doc = fitz.open()
            try:
                for i, page in enumerate(doc, 1):
                    if is_cancelled():
                        raise CancelledError("任务已取消")
                    pix = page.get_pixmap(dpi=dpi)
                    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                    buf = io.BytesIO()
                    im.save(buf, "JPEG", quality=quality)
                    rect = page.rect
                    new_page = new_doc.new_page(width=rect.width, height=rect.height)
                    new_page.insert_image(new_page.rect, stream=buf.getvalue())
                    on_progress(int(i / total * 100))
                new_doc.save(str(out), garbage=3, deflate=True)
            finally:
                new_doc.close()
    finally:
        doc.close()
    return in_size, Path(out).stat().st_size
