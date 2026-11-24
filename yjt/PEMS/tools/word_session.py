# -*- coding: utf-8 -*-
"""Word 后台自动化会话（跨项目复用，2026-11-24 定）。

背景：Word 是单实例 COM 服务器，直接 `DispatchEx` + `Quit` 或接管用户可见实例，
会导致用户正在编辑的窗口被关闭、窗口与任务栏反复闪现（`pitfalls.md` §128、§130）。

本模块统一方案：
1. 只用 `DispatchEx("Word.Application")` 起**独立隐藏实例**（实测为新进程、Visible=False、0 文档），
   不调用 `GetActiveObject`，绝不接管用户可见的 Word；
2. 整轮只保留一个会话（模块级缓存），`ScreenUpdating=False`，进程退出时统一恢复/退出；
3. 只关闭自己 `Documents.Open` 打开的文档；文档若已在会话里则复用、不关闭；
4. 导出 PDF 一律只读；刷新域需要写回时，若目标目录存在 `~$` 锁文件应提示用户先关闭。

用法：
    import word_session as W
    W.refresh_fields(r"D:\\out\\RD-001_V1.docx")
    pages = W.export_pdf(r"D:\\out\\RD-001_V1.docx", r"D:\\out\\RD-001_V1.pdf")
    W.quit_app()          # 可选；不调用也会在进程结束时自动收尾

后台运行（PowerShell，避免控制台窗口闪现）：
    Start-Process python -ArgumentList 'work\\closeout.py','--ver','V3','--dir','PEMS_V3' `
        -WindowStyle Hidden -Wait -RedirectStandardOutput closeout.log -RedirectStandardError closeout.err
"""
from __future__ import annotations

import atexit
import os
import time

_APP = {"app": None}


def get_app():
    """取得本轮唯一的隐藏 Word 实例（首次调用时创建）。"""
    if _APP["app"] is not None:
        return _APP["app"]
    import win32com.client as win32
    app = win32.DispatchEx("Word.Application")   # 独立进程，不是用户那个 Word
    try:
        app.Visible = False
        app.DisplayAlerts = 0
        app.ScreenUpdating = False
    except Exception:
        pass
    _APP["app"] = app
    atexit.register(quit_app)
    return app


def quit_app():
    """恢复屏幕刷新并退出本轮实例；只在本进程创建的实例上调用。"""
    app = _APP.get("app")
    if app is None:
        return
    try:
        app.ScreenUpdating = True
    except Exception:
        pass
    try:
        app.Quit()
    except Exception:
        pass
    _APP["app"] = None


def _find_open_doc(app, path):
    """目标文档已在本会话打开时返回它（避免重复打开、避免误关）。"""
    target = os.path.normcase(os.path.abspath(path))
    try:
        for d in app.Documents:
            try:
                if os.path.normcase(os.path.abspath(d.FullName)) == target:
                    return d
            except Exception:
                continue
    except Exception:
        pass
    return None


def open_doc(path, readonly=True):
    """打开文档，返回 (doc, opened_by_us)。打开的文档用 close_doc 关闭。"""
    app = get_app()
    doc = _find_open_doc(app, path)
    if doc is not None:
        return doc, False
    doc = app.Documents.Open(os.path.abspath(path), ReadOnly=bool(readonly),
                             AddToRecentFiles=False, Visible=False)
    return doc, True


def close_doc(doc, opened):
    """只关闭自己打开的文档；复用用户/前序步骤的文档时不关闭。"""
    if opened and doc is not None:
        try:
            doc.Close(False)
        except Exception:
            pass


def has_lock_files(folder):
    """目标目录存在 Word 锁文件（~$）时返回文件名列表，调用方应提示用户先关闭。"""
    try:
        return [f for f in os.listdir(folder) if f.startswith("~$")]
    except OSError:
        return []


def refresh_fields(path):
    """刷新正文域、TOC 与页眉页脚域后保存（会写回文档）。"""
    if has_lock_files(os.path.dirname(os.path.abspath(path))):
        raise RuntimeError("目标目录存在 Word 锁文件，请先关闭文档：%s" % path)
    doc, opened = open_doc(path, readonly=False)
    try:
        doc.Fields.Update()
        for toc in doc.TablesOfContents:
            toc.Update()
        for s in doc.Sections:
            for hf in (s.Headers, s.Footers):
                for i in range(1, hf.Count + 1):
                    hf(i).Range.Fields.Update()
        doc.Save()
    finally:
        close_doc(doc, opened)


def export_pdf(path, pdf, retries=3):
    """只读导出 PDF，返回页数。"""
    last = None
    for attempt in range(retries):
        try:
            doc, opened = open_doc(path, readonly=True)
            try:
                pages = int(doc.ComputeStatistics(2))
                doc.ExportAsFixedFormat(os.path.abspath(pdf), 17)
                return pages
            finally:
                close_doc(doc, opened)
        except Exception as e:      # Word 忙/被占用时重试
            last = e
            time.sleep(2 + attempt * 2)
    raise last
