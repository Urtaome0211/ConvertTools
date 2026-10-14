"""PDF 拆分：每页一文件 / 每 N 页一组 / 自定义页码范围。"""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf as fitz

from app.workers import CancelledError


def _parse_ranges(text: str, page_count: int) -> list[list[int]]:
    """解析 "1-3,5,7-" 形式的页码范围，返回每组页号（1 起始，闭区间）的列表。"""
    chunks: list[list[int]] = []
    for part in text.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d*)|(\d+)", part)
        if not m:
            raise ValueError(f"无法识别的页码表达式：{part!r}")
        if m.group(3) is not None:
            a = b = int(m.group(3))
        else:
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else page_count
        if a < 1 or b < 1:
            raise ValueError(f"页码必须从 1 开始：{part!r}")
        a = min(a, page_count)
        b = min(b, page_count)
        if a > b:
            raise ValueError(f"页码范围起止颠倒：{part!r}")
        chunks.append(list(range(a, b + 1)))
    return chunks


def split_pdf(src, out_dir: Path, mode: str = "single", every: int = 5,
              ranges: str = "",
              on_progress=None, on_log=None, is_cancelled=None) -> int:
    """拆分单个 PDF，结果写入 out_dir，返回生成文件数。

    mode: "single" 每页一文件 / "every" 每 N 页一组 / "ranges" 自定义范围。
    """
    on_progress = on_progress or (lambda _: None)
    on_log = on_log or (lambda _: None)
    is_cancelled = is_cancelled or (lambda: False)

    src_path = Path(src)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = src_path.stem
    doc = fitz.open(src_path)
    n_pages = len(doc)
    try:
        if mode == "single":
            groups = [[i] for i in range(1, n_pages + 1)]
            name = lambda idx: f"{stem}_p{groups[idx][0]:03d}.pdf"  # noqa: E731
        elif mode == "every":
            groups = [
                list(range(i, min(i + every, n_pages + 1)))
                for i in range(1, n_pages + 1, every)
            ]
            name = lambda idx: f"{stem}_part{idx + 1:03d}.pdf"  # noqa: E731
        else:
            groups = _parse_ranges(ranges, n_pages)
            if not groups:
                raise ValueError("请填写要导出的页码范围，例如：1-3,5,7-")
            name = lambda idx: f"{stem}_r{idx + 1:03d}.pdf"  # noqa: E731

        total = len(groups)
        for gi, pages in enumerate(groups, 1):
            if is_cancelled():
                raise CancelledError("任务已取消")
            out = out_dir / name(gi - 1)
            new_doc = fitz.open()
            try:
                new_doc.insert_pdf(doc, from_page=pages[0] - 1, to_page=pages[-1] - 1)
                new_doc.save(str(out), garbage=3, deflate=True)
            finally:
                new_doc.close()
            on_log(f"✓ {out.name}（第 {pages[0]}–{pages[-1]} 页）")
            on_progress(int(gi / total * 100))
    finally:
        doc.close()
    return total
