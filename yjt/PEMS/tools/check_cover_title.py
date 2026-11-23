# -*- coding: utf-8 -*-
"""封面大标题实测门禁：以 PDF 第 1 页渲染结果为准。

判据（注册人 2026-11-23 定）：
  - 第 1 页最大字号（磅）必须在 35.5~36.5；
  - 该字号的文字去掉空白后，必须等于文件名中的文档名（RD-0xx 之后、_Vn 之前）。

为什么不用 docx 的 w:sz：run 可以是"无显式字号"（继承 Normal 12pt），
读属性会得到空值而被跳过；PDF 读到的是最终渲染结果。

用法：
    python check_cover_title.py <docx目录> <pdf目录>
"""
import os
import re
import sys
from pathlib import Path

import fitz

SIZE_MIN, SIZE_MAX = 35.5, 36.5


def title_of(stem):
    name = re.sub(r"^RD-\d+\s+", "", stem)
    return re.sub(r"_V\d+$", "", name)


def main(argv):
    if len(argv) < 3:
        print("用法: check_cover_title.py <docx目录> <pdf目录>")
        return 2
    docx_dir, pdf_dir = Path(argv[1]), Path(argv[2])
    bad = []
    checked = 0
    for docx in sorted(docx_dir.glob("*.docx")):
        if docx.name.startswith("~$"):
            continue
        pdf = pdf_dir / (docx.stem + ".pdf")
        if not pdf.exists():
            bad.append("%s：无 PDF %s" % (docx.name, pdf.name))
            continue
        checked += 1
        doc = fitz.open(str(pdf))
        if not len(doc):
            bad.append("%s：PDF 无页面" % docx.name)
            continue
        sizes = []
        for block in doc[0].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["text"].strip():
                        sizes.append(span["size"])
        mx = max(sizes) if sizes else 0
        # 取接近最大字号的文字（容掉 0.6pt 的舍入差）
        txt = "".join(
            span["text"]
            for block in doc[0].get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span["text"].strip() and span["size"] >= mx - 0.6
        )
        txt = re.sub(r"[\s\u3000]+", "", txt)
        want = re.sub(r"[\s\u3000]+", "", title_of(docx.stem))
        if not (SIZE_MIN <= mx <= SIZE_MAX):
            bad.append("%s：封面最大字号 %.1fpt（应 %.0fpt）" % (docx.name, mx, SIZE_MAX - 0.5))
        if txt != want:
            bad.append("%s：封面标题「%s」≠「%s」" % (docx.name, txt[:24], want))

    if bad:
        print("封面标题门禁失败 %d 项：" % len(bad))
        for b in bad:
            print("  ×", b)
        return 1
    print("封面标题门禁通过：%d 份，PDF 实测 36pt 且标题=文档名" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
