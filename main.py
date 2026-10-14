"""ConvertTools 应用入口。

运行：py main.py
自检：py main.py --selftest（打包后的 ConvertTools.exe --selftest 同样支持，退出码 0 表示通过）
"""

import sys


def _selftest() -> int:
    """无界面自检：验证关键依赖、ffmpeg 与核心转换链路（供打包后回归）。"""
    import importlib
    import subprocess
    import tempfile
    from pathlib import Path

    results = []

    def check(name, fn):
        try:
            fn()
            results.append(f"[OK] {name}")
        except Exception as exc:  # noqa: BLE001
            results.append(f"[FAIL] {name} — {type(exc).__name__}: {exc}")

    def run_ok(cmd):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or "").strip()[:200])

    for mod in ("PySide6", "pymupdf", "pdf2docx", "pdfplumber", "openpyxl", "PIL", "win32com"):
        check(f"import {mod}", lambda m=mod: importlib.import_module(m))

    from app.core.ffmpeg import find_ffmpeg
    check("ffmpeg 可用", lambda: run_ok([find_ffmpeg(), "-version"]))

    def core_chain():
        import pymupdf
        tmp = Path(tempfile.mkdtemp(prefix="convert_selftest_"))
        pdf = tmp / "t.pdf"
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "ConvertTools selftest")
        doc.save(pdf)
        doc.close()
        from app.core.pdf_image import pdf_to_images
        if pdf_to_images(pdf, tmp / "img", "png", 72) != 1:
            raise RuntimeError("pdf_to_images 页数不对")
        from app.core.pdf_word import pdf_to_docx
        pdf_to_docx(pdf, tmp / "t.docx")
        if not (tmp / "t.docx").exists():
            raise RuntimeError("pdf_to_docx 无输出")
        from app.core.xlsx_pdf import pdf_to_xlsx
        pdf_to_xlsx(pdf, tmp / "t.xlsx")
        if not (tmp / "t.xlsx").exists():
            raise RuntimeError("pdf_to_xlsx 无输出")

    check("核心转换链路 (pdf→图片/docx/xlsx)", core_chain)
    text = "\n".join(results)
    log_path = Path(tempfile.gettempdir()) / "convertTools_selftest.log"
    try:
        log_path.write_text(text + "\n", encoding="utf-8")
    except OSError:
        pass
    if sys.stdout:
        print(text)
    return 0 if all(r.startswith("[OK]") for r in results) else 1


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from app import style
    from app.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("ConvertTools")
    app.setStyleSheet(style.QSS)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    raise SystemExit(main())
