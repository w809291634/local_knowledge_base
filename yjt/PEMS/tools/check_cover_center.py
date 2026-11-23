# -*- coding: utf-8 -*-
"""封面居中与 AI 标签门禁。

用法：
    python check_cover_center.py <docx目录> [--pdf <渲染目录>] [--tol 14]

判据（注册人 2026-11-23 实测确认）：
1. 第 1 页正文区（去掉页眉/页脚带，取页高 9%~91%）的上留白与下留白差 ≤ tol pt（默认 14pt，
   主文件「分类规则 -- 封面」第三条）；上下留白按渲染像素换算 pt，不按段落数估算；
2. 全包不得出现 AI 生成标识：`wp:docPr/@name="AILabel"` 图形 0 个，且 word/*.xml 不含
   「含 AI 生成／AI 生成／AI生成／AIGC／人工智能生成」等标记；
3. 任一文档缺渲染件按失败处理（未渲染不得判为通过）。

封面垂直居中的实现见 pitfalls §105：固定空行数不可靠，须按本脚本的渲染实测值迭代补/删
标题前空段（12pt 定长行便于收敛），不要用 `w:vAlign` 或单独分节。
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

TOL_PT = 14.0
DPI = 150
BAND = (0.09, 0.91)
MARKERS = ("含 AI 生成", "AI 生成", "AI生成", "AIGC", "人工智能生成", "大模型生成")


def ai_label_errors(docx_path: Path):
    errs = []
    d = Document(str(docx_path))
    n = 0
    for el in d.element.body.iter():
        if el.tag.endswith("}docPr") and "AILabel" in (el.get("name") or ""):
            n += 1
    if n:
        errs.append("%s 含 AILabel 图形 %d 处" % (docx_path.name, n))
    with zipfile.ZipFile(docx_path) as z:
        for part in z.namelist():
            if not (part.startswith("word/") and part.endswith(".xml")):
                continue
            text = z.read(part).decode("utf-8", "ignore")
            hits = [m for m in MARKERS if m in text]
            if hits:
                errs.append("%s %s 含 AI 生成标记：%s" % (docx_path.name, part, "、".join(hits)))
    return errs


def page1_blanks(pdf: Path):
    tmp = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-f", "1", "-l", "1",
                    str(pdf), os.path.join(tmp, "c")], capture_output=True)
    fs = sorted(glob.glob(os.path.join(tmp, "c*.png")))
    if not fs:
        return None
    from PIL import Image
    im = Image.open(fs[-1]).convert("L")
    w, h = im.size
    px = im.load()
    rows = [y for y in range(int(h * BAND[0]), int(h * BAND[1]))
            if any(px[x, y] < 200 for x in range(0, w, 3))]
    if not rows:
        return None
    pt = 72.0 / DPI
    return rows[0] * pt, (h - 1 - rows[-1]) * pt


def check(folder: str, pdfdir: str | None = None, tol: float = TOL_PT):
    errs = []
    folder = Path(folder)
    if pdfdir is None:
        pdfdir = folder / "render" / "V1"
    pdfdir = Path(pdfdir)
    for docx in sorted(folder.glob("RD-*.docx")):
        errs += ai_label_errors(docx)
        pdf = pdfdir / (docx.stem + ".pdf")
        if not pdf.exists():
            errs.append("%s 缺渲染件，封面居中未核" % docx.name)
            continue
        m = page1_blanks(pdf)
        if m is None:
            errs.append("%s 第 1 页无可测墨迹" % docx.name)
            continue
        top, bot = m
        if abs(top - bot) > tol:
            errs.append("%s 封面上留白 %.1fpt / 下留白 %.1fpt，差 %.1fpt > %.0fpt"
                        % (docx.name, top, bot, abs(top - bot), tol))
    return errs


def main(argv):
    if not argv:
        print("用法：python check_cover_center.py <docx目录> [--pdf <渲染目录>] [--tol 14]")
        return 1
    pdfdir, tol, targets = None, TOL_PT, []
    i = 0
    while i < len(argv):
        if argv[i] == "--pdf" and i + 1 < len(argv):
            pdfdir = argv[i + 1]; i += 2; continue
        if argv[i] == "--tol" and i + 1 < len(argv):
            tol = float(argv[i + 1]); i += 2; continue
        targets.append(argv[i]); i += 1
    errs = []
    for t in targets:
        errs += check(t, pdfdir, tol)
    if errs:
        print("封面居中／AI 标签门禁失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("封面居中／AI 标签门禁通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
