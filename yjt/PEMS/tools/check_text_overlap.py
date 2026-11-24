# -*- coding: utf-8 -*-
"""渲染重叠门禁：同一页上的文字行不得互相压叠。

背景（2026-11-24）：029 第九章的浮动表单靠空段占位；空段被清掉后正文压到表单行上，
docx 层看不出问题。本判据读 PDF：同一页任意两行文字的包围盒若纵向重叠超过 50%
且横向重叠超过较窄行的 30%，即判为重叠（正常相邻行、分栏、表格同格多行不会命中）。

用法：python check_text_overlap.py <产物目录> --pdf <渲染目录>
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

V_OVER = 0.5
H_OVER = 0.3


def lines(page):
    out = []
    h = page.rect.height
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            b = line["bbox"]
            if b[3] < h * 0.06 or b[1] > h * 0.94:
                continue
            txt = "".join(s["text"] for s in line.get("spans", [])).strip()
            if txt:
                out.append((b, txt))
    return out


def check_pdf(pdf: Path):
    errs = []
    doc = fitz.open(str(pdf))
    for pno, page in enumerate(doc, start=1):
        ls = lines(page)
        for i in range(len(ls)):
            bi, ti = ls[i]
            for j in range(i + 1, len(ls)):
                bj, tj = ls[j]
                v = min(bi[3], bj[3]) - max(bi[1], bj[1])
                if v <= 0:
                    continue
                hi = bi[3] - bi[1]
                hj = bj[3] - bj[1]
                if v < min(hi, hj) * V_OVER:
                    continue
                hov = min(bi[2], bj[2]) - max(bi[0], bj[0])
                if hov <= 0:
                    continue
                if hov < min(bi[2] - bi[0], bj[2] - bj[0]) * H_OVER:
                    continue
                errs.append("%s 第%d页 文字重叠：「%s」与「%s」"
                            % (pdf.name, pno, ti[:24], tj[:24]))
                break
    return errs


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opt = {a.split("=", 1)[0][2:]: a.split("=", 1)[1]
           for a in argv if a.startswith("--") and "=" in a}
    if not args or "pdf" not in opt:
        print("用法：check_text_overlap.py <产物目录> --pdf=<渲染目录>")
        return 2
    prod, pdfdir = Path(args[0]), Path(opt["pdf"])
    errs = []
    for f in sorted(prod.glob("RD-*.docx")):
        if f.name.startswith("~$"):
            continue
        pdf = pdfdir / (f.stem + ".pdf")
        if not pdf.exists():
            errs.append("%s 缺渲染件：%s" % (f.name, pdf.name))
            continue
        errs += check_pdf(pdf)
    if errs:
        print("渲染重叠门禁失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("渲染重叠门禁通过：未发现文字行互相压叠")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
