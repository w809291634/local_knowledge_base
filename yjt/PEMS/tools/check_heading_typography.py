# -*- coding: utf-8 -*-
"""标题排版门禁：一级16pt / 二级14pt / 三级12pt，加粗、左对齐、编号后一个空格。

判据来源：`reference-document-format-and-diagram-requirements.md`「分类规则 -- 字号」、
`pitfalls.md` §97③（编号与文字间留一个空格）与「分类规则 -- 标题树」（左对齐零缩进）。

用法：python check_heading_typography.py <产物目录>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docx_ops as ops

SZ = {0: "32", 1: "28", 2: "24"}
NUM_SPACE = re.compile(r"^(第[一二三四五六七八九十]+(?:章|部分)|\d+(?:\.\d+)*)(\s*)(\S)")


def is_bold(p):
    if any(bool(r.bold) for r in p.runs if r.text.strip()):
        return True
    st, seen = p.style, 0
    while st is not None and seen < 10:
        if st.font.bold:
            return True
        st = st.base_style
        seen += 1
    return False


def check_doc(path: Path):
    errs = []
    d = docx.Document(str(path))
    kids = list(d.element.body.iterchildren())
    cover = -1
    for i, el in enumerate(kids):
        if el.tag == qn("w:tbl") and "文件编号" in "".join(
                t.text or "" for t in el.iter(qn("w:t"))):
            cover = i
            break
    pre = set(id(x) for x in kids[:cover + 1])
    for p in d.paragraphs:
        if id(p._p) in pre:
            continue
        t = p.text.strip()
        if not t or "\t" in p.text or re.fullmatch(r"目\s*录", t):
            continue
        if (p.style.name or "").lower().startswith("toc") or re.search(r"\.{3,}\s*\d+\s*$", t):
            continue
        lv = ops.effective_outline_level(p)
        if lv is None or lv > 2:
            continue
        if not (p.style.name or "").lower().startswith("heading") and len(t) > 30:
            continue
        sz = ops._effective_sz(p._p, d)
        if sz != SZ[lv]:
            errs.append("%s %d级标题字号 %s（应 %s）：%s"
                        % (path.name, lv, sz, SZ[lv], t[:24]))
        if not is_bold(p):
            errs.append("%s %d级标题未加粗：%s" % (path.name, lv, t[:24]))
        m = NUM_SPACE.match(t)
        if m and m.group(2) != " ":
            errs.append("%s 编号与标题间应为一个半角空格：%s" % (path.name, t[:24]))
        if p.alignment not in (None, 0):
            errs.append("%s 标题应左对齐：%s" % (path.name, t[:24]))
    return errs


def main(argv):
    if not argv:
        print("用法：check_heading_typography.py <产物目录>")
        return 2
    root = Path(argv[0])
    errs = []
    for f in sorted(root.glob("RD-*.docx")):
        if f.name.startswith("~$"):
            continue
        errs += check_doc(f)
    if errs:
        print("标题排版门禁失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("标题排版门禁通过：16/14/12pt、加粗、左对齐、编号后一个空格")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
