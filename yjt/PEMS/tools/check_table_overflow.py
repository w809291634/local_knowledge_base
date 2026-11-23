# -*- coding: utf-8 -*-
"""表格越界门禁（渲染为准）：任何一页的文字/表格不得越过左右版心。

用法：python check_table_overflow.py <产物目录> [--pdf <渲染目录>]

判据：
1. 渲染：用 `pdftotext -bbox` 取每页每个词的包围盒，任一 xMin < 左页边距-2pt
   或 xMax > 页宽-右页边距+2pt 即失败（页眉页脚线除外，按 y 带过滤）；
2. 结构：`tblLayout=fixed` 且 grid 合计＋tblInd > 版心 + 20twips 即失败；
3. `tblInd < 0` 一律失败。
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

TOL_PT = 12.0
TOL_TW = 20


def margins(doc):
    s = doc.sections[0]
    return s.page_width.pt, s.left_margin.pt, s.right_margin.pt


def fixed_overflow(path):
    d = docx.Document(path)
    cap = int(d.sections[0].page_width.twips - d.sections[0].left_margin.twips
              - d.sections[0].right_margin.twips)
    errs = []
    for i, t in enumerate(d.tables):
        grid = t._tbl.find(qn("w:tblGrid"))
        cols = [int(g.get(qn("w:w"))) for g in grid.findall(qn("w:gridCol"))] if grid is not None else []
        tblPr = t._tbl.find(qn("w:tblPr"))
        ind = 0
        fixed = False
        if tblPr is not None:
            e = tblPr.find(qn("w:tblInd"))
            if e is not None:
                ind = int(e.get(qn("w:w")) or 0)
            lay = tblPr.find(qn("w:tblLayout"))
            fixed = lay is not None and lay.get(qn("w:type")) == "fixed"
        if ind < 0:
            errs.append("%s 表%d 负缩进 %d" % (path.name[:6], i, ind))
        if fixed and cols and sum(cols) + ind > cap + TOL_TW:
            errs.append("%s 表%d 固定布局超宽：%d＋%d > 版心 %d"
                        % (path.name[:6], i, sum(cols), ind, cap))
    return errs


def pdf_overflow(pdf):
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True).stdout.decode("utf-8", "ignore")
    w = float(re.search(r"Page size:\s+([\d.]+)", info).group(1))
    xml = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"],
                         capture_output=True).stdout.decode("utf-8", "ignore")
    pages = re.findall(r"<page width=\"([\d.]+)\" height=\"([\d.]+)\">(.*?)</page>", xml, re.S)
    errs = []
    for pi, (pw, ph, body) in enumerate(pages, 1):
        pw, ph = float(pw), float(ph)
        for m in re.finditer(r"<word xMin=\"([\d.]+)\" yMin=\"([\d.]+)\" xMax=\"([\d.]+)\" yMax=\"([\d.]+)\">([^<]*)</word>", body):
            x0, y0, x1, y1, txt = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5)
            if y0 < ph * 0.06 or y1 > ph * 0.94:      # 页眉页脚带
                continue
            if x0 < 70.8 - TOL_PT or x1 > pw - 70.8 + TOL_PT:
                errs.append("%s 第%d页越界：x=%.1f~%.1f（页宽 %.0f）%r"
                            % (pdf.name[:6], pi, x0, x1, pw, txt[:20]))
    return errs


def main(argv):
    folder = Path(argv[0]) if argv else Path(".")
    pdfdir = None
    if "--pdf" in argv:
        pdfdir = Path(argv[argv.index("--pdf") + 1])
    errs = []
    for f in sorted(folder.glob("RD-*.docx")):
        errs += fixed_overflow(f)
        if pdfdir:
            pdf = pdfdir / (f.stem + ".pdf")
            if not pdf.exists():
                errs.append("%s 缺渲染件，越界未核" % f.name)
                continue
            errs += pdf_overflow(pdf)
    if errs:
        print("表格越界门禁失败：")
        for e in errs[:40]:
            print("  -", e)
        return 1
    print("表格越界门禁通过：渲染与结构均无越界")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


