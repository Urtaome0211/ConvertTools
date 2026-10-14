"""PDF ⇄ 图片 转换。

- PDF → 图片：PyMuPDF 逐页渲染为 PNG/JPG（可设 DPI）
- 图片 → PDF：Pillow 将多张图片按文件名排序合成一个 PDF
"""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
from PIL import Image

from app.workers import CancelledError

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def pdf_to_images(pdf, out_dir: Path, fmt: str = "png", dpi: int = 150,
                  on_progress=None, on_log=None, is_cancelled=None) -> int:
    """把 PDF 每一页渲染成图片，写入 out_dir，返回图片张数。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(pdf).stem
    doc = fitz.open(pdf)
    total = len(doc)
    try:
        for i, page in enumerate(doc, 1):
            if is_cancelled():
                raise CancelledError("任务已取消")
            pix = page.get_pixmap(dpi=dpi)
            out = out_dir / f"{stem}_p{i:03d}.{fmt}"
            pix.save(str(out))
            on_progress(int(i / total * 100))
    finally:
        doc.close()
    return total


def images_to_pdf(paths, out: Path,
                  on_progress=None, on_log=None, is_cancelled=None) -> int:
    """把多张图片按文件名排序合成一个 PDF，返回图片张数。"""
    on_progress = on_progress or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    paths = sorted(paths, key=lambda p: Path(p).name.lower())
    frames = []
    for i, p in enumerate(paths, 1):
        if is_cancelled():
            raise CancelledError("任务已取消")
        with Image.open(p) as im:
            im.load()
            frames.append(im.convert("RGB").copy())
        on_progress(int(i / len(paths) * 100))
    if not frames:
        raise ValueError("没有可用图片")
    frames[0].save(str(out), save_all=True, append_images=frames[1:], resolution=150.0)
    return len(frames)
