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
NUM_SPACE = re.compile(r"^(第[一二三四五六七八九十]+(?:章|部分)|[0-9]+(?:\.[0-9]+)*\.?)(\s*)(\S)")
TOC_LEAD = re.compile(r"^(.*?)(?:\t|\.{3,})")


def toc_head(t):
    """取目录条目在制表符/点线之前的标题文字（页码与域不受影响）。"""
    m = TOC_LEAD.match(t)
    return (m.group(1) if m else t).strip()


def bad_gap(m):
    """编号与标题之间必须恰好一个半角空格；编号后紧跟标点（如「1》」）不算缺空格。"""
    gap, nxt = m.group(2), m.group(3)
    if gap == " ":
        return False
    return bool(gap.strip()) or bool(re.match(r"[\u4e00-\u9fa5A-Za-z0-9]", nxt))


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


def eff_line(p):
    """标题有效行距：段落直接 -> 样式链，返回 (line, rule)。"""
    pPr = p._p.find(qn("w:pPr"))
    sp = pPr.find(qn("w:spacing")) if pPr is not None else None
    if sp is not None and sp.get(qn("w:line")) is not None:
        return sp.get(qn("w:line")), sp.get(qn("w:lineRule"))
    st, seen = p.style, 0
    while st is not None and seen < 10:
        spp = st.element.find(qn("w:pPr"))
        s2 = spp.find(qn("w:spacing")) if spp is not None else None
        if s2 is not None and s2.get(qn("w:line")) is not None:
            return s2.get(qn("w:line")), s2.get(qn("w:lineRule"))
        st = st.base_style
        seen += 1
    return None, None


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
        if not t or re.fullmatch(r"目\s*录", t):
            continue
        if ("\t" in p.text or (p.style.name or "").lower().startswith("toc")
                or re.search(r"\.{3,}\s*\d+\s*$", t)
                or ops.effective_outline_level(p) == 9):
            # 目录条目：只校验编号后空格，页码/域不参与
            head = toc_head(t)
            m = NUM_SPACE.match(head)
            if m and bad_gap(m):
                errs.append("%s 目录条目编号与标题间应为一个半角空格：%s"
                            % (path.name, head[:24]))
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
        line, rule = eff_line(p)
        if line and ((rule in (None, "auto") and int(line) > 260)
                     or (rule in ("exact", "atLeast") and int(line) > 320)):
            errs.append("%s %d级标题行距过大（line=%s %s，应单倍 240）：%s"
                        % (path.name, lv, line, rule or "auto", t[:24]))
        m = NUM_SPACE.match(t)
        if m and bad_gap(m):
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
