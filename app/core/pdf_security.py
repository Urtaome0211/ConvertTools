"""PDF 加密、解密与水印。"""

from __future__ import annotations

import io
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont

from app.workers import CancelledError


def encrypt_pdf(src, out, password: str,
                on_progress=None, on_log=None, is_cancelled=None) -> None:
    """AES-256 口令加密，保留打印与复制权限。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    doc = fitz.open(src)
    try:
        if is_cancelled():
            raise CancelledError("任务已取消")
        doc.save(
            str(out),
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw=password,
            user_pw=password,
            permissions=fitz.PDF_PERM_PRINT | fitz.PDF_PERM_COPY,
            garbage=3,
            deflate=True,
        )
        on_log(f"已加密：{Path(src).name} → {Path(out).name}（AES-256）")
    finally:
        doc.close()
    on_progress(100)


def decrypt_pdf(src, out, password: str,
                on_progress=None, on_log=None, is_cancelled=None) -> None:
    """移除 PDF 口令保护。"""
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    doc = fitz.open(src)
    try:
        if doc.needs_pass and not doc.authenticate(password):
            raise ValueError("密码错误，无法解密该 PDF")
        if is_cancelled():
            raise CancelledError("任务已取消")
        doc.save(str(out), encryption=fitz.PDF_ENCRYPT_NONE, garbage=3, deflate=True)
        on_log(f"已解密：{Path(src).name} → {Path(out).name}")
    finally:
        doc.close()
    on_progress(100)


def watermark_pdf(src, out, text: str = "", image_path: str = "",
                  font_size: int = 48, opacity: float = 0.15, angle: int = 45,
                  on_progress=None, on_log=None, is_cancelled=None) -> int:
    """给 PDF 每页加文字或图片水印（居中），返回页数。

    水印先用 Pillow 渲染成透明底 PNG（支持任意角度旋转），再逐页插入，
    避免 PyMuPDF insert_text 的 rotate 参数仅支持 90° 倍数的问题。
    """
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    if not text and not image_path:
        raise ValueError("请填写水印文字或选择水印图片")

    alpha_val = max(0, min(255, int(opacity * 255)))
    if text:
        try:
            font = ImageFont.truetype("msyh.ttc", font_size)
        except OSError:
            font = ImageFont.load_default()
        probe = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        pd = ImageDraw.Draw(probe)
        bbox = pd.textbbox((0, 0), text, font=font)
        pad = font_size // 2
        wm = Image.new("RGBA", (bbox[2] - bbox[0] + pad * 2,
                                bbox[3] - bbox[1] + pad * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(wm)
        d.text((pad - bbox[0], pad - bbox[1]), text, font=font,
               fill=(110, 115, 125, alpha_val))
    else:
        with Image.open(image_path) as im:
            im.load()
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            alpha = im.getchannel("A").point(lambda v: int(v * opacity))
            im.putalpha(alpha)
            max_dim = 1200
            if max(im.size) > max_dim:
                im.thumbnail((max_dim, max_dim), Image.LANCZOS)
            wm = im
    wm = wm.rotate(angle, expand=True, resample=Image.BICUBIC)
    buf = io.BytesIO()
    wm.save(buf, "PNG")
    img_bytes = buf.getvalue()

    doc = fitz.open(src)
    total = len(doc)
    try:
        for i, page in enumerate(doc, 1):
            if is_cancelled():
                raise CancelledError("任务已取消")
            pm = fitz.Pixmap(img_bytes)
            rect = page.rect
            scale = min(rect.width, rect.height) * 0.45 / max(pm.width, pm.height)
            w = pm.width * scale
            h = pm.height * scale
            ir = fitz.Rect(
                (rect.width - w) / 2, (rect.height - h) / 2,
                (rect.width + w) / 2, (rect.height + h) / 2,
            )
            page.insert_image(ir, pixmap=pm, overlay=True)
            on_progress(int(i / total * 100))
        doc.save(str(out), garbage=3, deflate=True)
        on_log(f"已加水印：{Path(src).name} → {Path(out).name}")
    finally:
        doc.close()
    return total
