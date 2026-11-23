# -*- coding: utf-8 -*-
"""表格越界门禁（结构 + 渲染双口径）。

用法：python check_table_overflow.py <产物目录> [--pdf <渲染目录>] [--skip-tables "标记1,标记2"]

判据：
1. 结构：按表格**所属节**取版心（横竖版混排不能一律用第 1 节）；
   - `tblInd < 0` 一律失败；
   - `tblW`（dxa）> 版心 + 12pt 失败——Word 按 tblW 渲染，列宽和正常也会溢出；
   - `tblLayout=fixed` 且 列宽和＋缩进 > 版心 + 12pt 失败；
   - `tblLayout=fixed` 且 `tblW` 与列宽和相差 > max(50, 2%) 失败（V6 052 §2.5.6 即此形态）；
   - 封面信息表（首格「文件编号」）跳过：模板浮动居中表，宽度按模板保留。
2. 渲染：`pdftotext -bbox` 取每页词框，按**该页所属节**的左右页边距判断（容差 12pt）；
   页眉页脚带按 y 比例过滤。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx_ops as ops

TOL_PT = 12.0
TOL_TW = 240                      # 12pt，与渲染容差一致


def section_boxes(doc):
    return [(s.page_width.pt, s.page_height.pt, s.left_margin.pt, s.right_margin.pt)
            for s in doc.sections]


def structural(path, skip_markers=()):
    """结构层：tblW / 列宽和 / 缩进 / 负缩进。"""
    d = docx.Document(str(path))
    caps = ops.table_section_caps(d)
    etxt = lambda el: "".join(t.text or "" for t in el.iter(qn("w:t")))
    cover = next((c for c in d.element.body.iterchildren()
                  if c.tag.split("}")[-1] == "tbl" and "文件编号" in etxt(c)), None)
    errs = []
    for i, t in enumerate(d.tables):
        if t._tbl is cover:
            continue
        if any(m in etxt(t._tbl) for m in skip_markers):
            continue
        cap = caps[i] if i < len(caps) else (caps[0] if caps else 9072)
        tbl = t._tbl
        tblPr = tbl.find(qn("w:tblPr"))
        ind, fixed, tw_type, twv = 0, False, None, None
        if tblPr is not None:
            e = tblPr.find(qn("w:tblInd"))
            if e is not None:
                ind = int(e.get(qn("w:w")) or 0)
            lay = tblPr.find(qn("w:tblLayout"))
            fixed = lay is not None and (lay.get(qn("w:type")) or "") == "fixed"
            tw = tblPr.find(qn("w:tblW"))
            if tw is not None:
                tw_type = tw.get(qn("w:type")) or "dxa"
                twv = int(tw.get(qn("w:w")) or 0)
        grid = tbl.find(qn("w:tblGrid"))
        cols = ([int(c.get(qn("w:w")) or 0) for c in grid.findall(qn("w:gridCol"))]
                if grid is not None else [])
        tot = sum(cols)
        tag = "%s 表%d" % (path.name[:6], i + 1)
        if ind < 0:
            errs.append("%s 负缩进 %d" % (tag, ind))
        if fixed and tw_type == "dxa" and twv and twv > cap + TOL_TW:
            errs.append("%s tblW=%d > 版心 %d（整表溢出）" % (tag, twv, cap))
        if fixed and cols and tw_type in ("dxa", "auto") and tot + ind > cap + TOL_TW:
            errs.append("%s 固定布局超宽：列宽和 %d＋缩进 %d > 版心 %d"
                        % (tag, tot, ind, cap))
        if fixed and cols and tw_type == "dxa" and twv \
                and abs(twv - tot) > max(50, int(tot * 0.02)):
            errs.append("%s tblW=%d 与列宽和 %d 不一致（Word 按 tblW 渲染）"
                        % (tag, twv, tot))
    return errs


def pdf_overflow(pdf, boxes):
    """渲染层：按每页尺寸匹配所属节的页边距。"""
    xml = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"],
                         capture_output=True).stdout.decode("utf-8", "ignore")
    pages = re.findall(r"<page width=\"([\d.]+)\" height=\"([\d.]+)\">(.*?)</page>", xml, re.S)
    if not pages:
        return ["%s 渲染层未解析出页面（检查 pdftotext 是否可用）" % pdf.name[:6]]
    errs = []
    for pi, (pw, ph, body) in enumerate(pages, 1):
        pw, ph = float(pw), float(ph)
        box = next((b for b in boxes
                    if abs(b[0] - pw) <= 1.0 and abs(b[1] - ph) <= 1.0), None)
        rm = box[3] if box else 70.8
        for m in re.finditer(
                r"<word xMin=\"([\d.]+)\" yMin=\"([\d.]+)\" xMax=\"([\d.]+)\" "
                r"yMax=\"([\d.]+)\">([^<]*)</word>", body):
            x0, y0, x1, y1, txt = (float(m.group(1)), float(m.group(2)),
                                   float(m.group(3)), float(m.group(4)), m.group(5))
            if y0 < ph * 0.06 or y1 > ph * 0.94:      # 页眉页脚带
                continue
            if x0 < (box[2] if box else 70.8) - TOL_PT or x1 > pw - rm + TOL_PT:
                errs.append("%s 第%d页越界：x=%.1f~%.1f（页宽 %.0f，右界 %.1f）%r"
                            % (pdf.name[:6], pi, x0, x1, pw, pw - rm, txt[:20]))
    return errs


def main(argv):
    folder = Path(argv[0]) if argv and not argv[0].startswith("--") else Path(".")
    pdfdir = Path(argv[argv.index("--pdf") + 1]) if "--pdf" in argv else None
    skip = ()
    if "--skip-tables" in argv:
        skip = tuple(x.strip() for x in argv[argv.index("--skip-tables") + 1].split(",")
                     if x.strip())
    errs = []
    for f in sorted(folder.glob("RD-*.docx")):
        errs += structural(f, skip)
        if pdfdir:
            pdf = pdfdir / (f.stem + ".pdf")
            if not pdf.exists():
                errs.append("%s 缺渲染件，越界未核" % f.name)
                continue
            errs += pdf_overflow(pdf, section_boxes(docx.Document(str(f))))
    if errs:
        print("表格越界门禁失败：")
        for e in errs[:40]:
            print("  -", e)
        return 1
    print("表格越界门禁通过：tblW/列宽和/负缩进与渲染文字均未越界")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
