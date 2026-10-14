"""图片格式互转与压缩。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.core.pdf_image import IMAGE_EXTS
from app.workers import CancelledError

OUTPUT_FORMATS = ("jpg", "png", "webp", "bmp", "tiff")
RESIZE_MODES = ("不缩放", "按宽度", "按高度", "长边限制", "按百分比")
LOSSLESS_FORMATS = {"png", "bmp", "tiff"}


def _apply_resize(im: Image.Image, mode: str, value: int) -> Image.Image:
    if mode == "不缩放":
        return im
    w, h = im.size
    if mode == "按百分比":
        value = max(1, min(400, value))
        nw, nh = max(1, int(w * value / 100)), max(1, int(h * value / 100))
    elif mode == "按宽度":
        nw, nh = value, max(1, int(h * value / w))
    elif mode == "按高度":
        nw, nh = max(1, int(w * value / h)), value
    else:  # 长边限制
        if max(w, h) <= value:
            return im
        if w >= h:
            nw, nh = value, max(1, int(h * value / w))
        else:
            nw, nh = max(1, int(w * value / h)), value
    return im.resize((nw, nh), Image.LANCZOS)


def convert_image(src, out: Path, fmt: str, quality: int = 90,
                  resize_mode: str = "不缩放", resize_value: int = 100,
                  on_progress=None, on_log=None, is_cancelled=None) -> tuple[int, int]:
    """转换单张图片格式，返回 (原始字节数, 输出字节数)。"""
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    if is_cancelled():
        raise CancelledError("任务已取消")
    in_size = Path(src).stat().st_size
    with Image.open(src) as im:
        im.load()
        keep_alpha = fmt in ("png", "webp")
        if im.mode == "LA":
            im = im.convert("RGBA")
        if im.mode == "RGBA" and not keep_alpha:
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.getchannel("A"))
            im = bg
        elif im.mode == "P":
            im = im.convert("RGBA" if keep_alpha and "transparency" in im.info else "RGB")
        elif im.mode not in ("RGB", "RGBA", "L"):
            im = im.convert("RGB")
        im = _apply_resize(im, resize_mode, resize_value)

        if fmt == "jpg":
            im.convert("RGB").save(out, "JPEG", quality=quality, optimize=True)
        elif fmt == "webp":
            im.save(out, "WEBP", quality=quality)
        elif fmt == "png":
            im.save(out, "PNG", optimize=True)
        elif fmt == "tiff":
            im.save(out, "TIFF", compression="tiff_lzw")
        else:  # bmp
            im.convert("RGB").save(out, "BMP")
    out_size = out.stat().st_size
    on_log(f"转换完成：{Path(src).name} → {out.name}")
    return in_size, out_size
