"""通过 MS Office COM 自动化完成 Word/Excel → PDF 转换。

要求：本机安装 Microsoft Word / Excel。
COM 调用必须在 CoInitialize 的线程中进行（转换任务运行在子线程）。
"""

from __future__ import annotations

from pathlib import Path

wdFormatPDF = 17  # Word 导出格式枚举：PDF
xlTypePDF = 0     # Excel 导出格式枚举：PDF


def docx_to_pdf(src, out, on_progress=None, on_log=None, is_cancelled=None) -> None:
    """Word (.docx/.doc) → PDF，保真度最高。"""
    on_log = on_log or (lambda _: None)
    on_progress = on_progress or (lambda _: None)
    on_log(f"调用 MS Word 转换：{Path(src).name} …")
    on_progress(None)  # COM 转换无法汇报进度

    import pythoncom
    from win32com.client import DispatchEx

    pythoncom.CoInitialize()
    word = None
    try:
        word = DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(str(Path(src).resolve()), ReadOnly=True)
        try:
            doc.ExportAsFixedFormat(str(Path(out).resolve()), wdFormatPDF)
        finally:
            doc.Close(False)
    finally:
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()
    on_progress(100)


def xlsx_to_pdf(src, out, on_progress=None, on_log=None, is_cancelled=None) -> None:
    """Excel (.xlsx/.xls) → PDF，保留打印布局与分页。"""
    on_log = on_log or (lambda _: None)
    on_progress = on_progress or (lambda _: None)
    on_log(f"调用 MS Excel 转换：{Path(src).name} …")
    on_progress(None)

    import pythoncom
    from win32com.client import DispatchEx

    pythoncom.CoInitialize()
    xl = None
    try:
        xl = DispatchEx("Excel.Application")
        xl.Visible = False
        xl.DisplayAlerts = False
        wb = xl.Workbooks.Open(str(Path(src).resolve()))
        try:
            wb.ExportAsFixedFormat(xlTypePDF, str(Path(out).resolve()))
        finally:
            wb.Close(False)
    finally:
        if xl is not None:
            xl.Quit()
        pythoncom.CoUninitialize()
    on_progress(100)
