# -*- coding: utf-8 -*-
"""空章节检查：标题后至下一标题前必须有一段正文、一张表或一张图。

判定口径（注册人 2026-11-23 定）：
- **每个标题都必须有正文/表/图**，包括章标题和容器章；
- 容器章（下接更深一级节标题）也至少要有 1 句引导语，否则判空；
- 目录条目（toc 样式）、空标题段、封面文档名不参与判定。

用法：python tools/check_empty_sections.py <产物目录或 docx...>
非零退出表示存在空章节。
"""
import os
import sys
import glob

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

W_P = qn("w:p")
W_TBL = qn("w:tbl")


def heading_level(p):
    st = p.style.name if p.style is not None else ""
    if st.startswith("Heading "):
        try:
            return int(st.split()[1])
        except ValueError:
            return 1
    if st.lower().startswith("toc"):
        return 0
    ppr = p._p.pPr
    if ppr is not None:
        ol = ppr.find(qn("w:outlineLvl"))
        if ol is not None:
            try:
                return int(ol.get(qn("w:val"))) + 1
            except (TypeError, ValueError):
                return 0
    return 0


def has_image(p):
    return bool(p._p.findall(".//" + qn("a:blip")) or p._p.findall(".//" + qn("w:pict")))


def check_doc(path):
    d = Document(path)
    items = []
    for child in d.element.body.iterchildren():
        if child.tag == W_P:
            items.append(("p", Paragraph(child, d)))
        elif child.tag == W_TBL:
            items.append(("tbl", child))

    heads = []
    for i, (typ, obj) in enumerate(items):
        if typ != "p":
            continue
        lvl = heading_level(obj)
        t = obj.text.strip()
        if lvl and t:
            heads.append((i, lvl, t))

    errs = []
    for n, (i, lvl, t) in enumerate(heads):
        j = heads[n + 1][0] if n + 1 < len(heads) else len(items)
        content = False
        for k in range(i + 1, j):
            typ, obj = items[k]
            if typ == "tbl" or (obj.text.strip() or has_image(obj)):
                content = True
                break
        if content:
            continue
        errs.append((os.path.basename(path), t, lvl))
    return errs


def expand(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out.extend(sorted(glob.glob(os.path.join(p, "RD-*.docx"))))
        elif os.path.isfile(p) and p.lower().endswith(".docx"):
            out.append(p)
        else:
            print("跳过非目录/非 docx：%s" % p)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    files = expand(argv)
    if not files:
        print("未找到 docx")
        return 2
    all_errs = []
    for f in files:
        errs = check_doc(f)
        if errs:
            all_errs.extend(errs)
            print("FAIL %s" % os.path.basename(f))
            for _, t, lvl in errs:
                print("  - 空章节（%d 级）：%s" % (lvl, t))
        else:
            print("PASS %s" % os.path.basename(f))
    if all_errs:
        print("空章节检查失败：%d 处" % len(all_errs))
        return 1
    print("空章节检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
