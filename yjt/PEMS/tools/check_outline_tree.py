# -*- coding: utf-8 -*-
"""标题树门禁（注册人 2026-11-23 定：所有 PEMS 文档都必须有标题树）。

用法：python check_outline_tree.py <产物目录>

判据：
1. 每份文档正文（非封面大标题、非表格单元格）至少 1 个 `outlineLvl=0`，且标题总数 ≥2；
2. 层级与编号形态一致：第X部分/第X章/一、→0，X.X→1，X.X.X 及更深→2；
3. 同名标题在同层级只能出现一次（静态目录条目混入正文会命中）；
4. 静态目录条目（含点线引导符或 toc 样式）必须为 9 级；表格单元格不得为 0~8；
5. 层级不得断层（首个正文标题必须为 0，下一级不得比上一级深超过 1 层）；
6. 编号顺序倒退只告警（多为内容排版问题，另行处理）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
P_PART = re.compile(r"^第[一二三四五六七八九十]+(部分|章)")
P_CN = re.compile(r"^[一二三四五六七八九十]+、")
P_L3 = re.compile(r"^\d+\.\d+\.\d+")
P_L2 = re.compile(r"^\d+\.\d+")
P_NUM_DOT = re.compile(r"^\d+\.(?!\d)")
P_NUM = re.compile(r"^(\d+(?:\.\d+)*)")
TOC_DOTS = re.compile(r"\.{4,}")


def lvl(p):
    pPr = p._p.find(qn("w:pPr"))
    if pPr is None:
        return None
    e = pPr.find(qn("w:outlineLvl"))
    return int(e.get(qn("w:val"))) if e is not None else None


def size_of(p):
    ss = [r.font.size.pt for r in p.runs if r.font.size]
    return max(ss) if ss else 0


def norm(t):
    return re.sub(r"\s+", " ", t.strip())


def check_doc(path: Path):
    errs, warns = [], []
    d = Document(str(path))
    heads = []
    for p in d.paragraphs:
        lv = lvl(p)
        t = p.text.strip()
        toc = (p.style.name or "").lower().startswith("toc") or bool(TOC_DOTS.search(t))
        if toc and lv is not None and lv < 9:
            errs.append("%s 静态目录条目仍为 %d 级：%s" % (path.name, lv, norm(t)[:30]))
            continue
        if not t or lv is None or lv >= 9:
            continue
        if size_of(p) >= 30:
            continue
        heads.append((lv, norm(t)))
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    lv = lvl(p)
                    if lv is not None and lv < 9:
                        errs.append("%s 表格单元格内出现 %d 级大纲：%s"
                                    % (path.name, lv, norm(p.text)[:20]))
    if not [h for h in heads if h[0] == 0]:
        errs.append("%s 正文没有一级标题（标题树缺失）" % path.name)
    if len(heads) < 2:
        errs.append("%s 标题总数 %d < 2" % (path.name, len(heads)))
    seen = {}
    for lv, t in heads:
        seen.setdefault((lv, t), 0)
        seen[(lv, t)] += 1
    for (lv, t), n in seen.items():
        if n > 1:
            errs.append("%s 同名标题重复 %d 次（%d 级）：%s" % (path.name, n, lv, t[:30]))
    for lv, t in heads:
        want = None
        if P_PART.match(t) or P_CN.match(t):
            want = 0
        elif P_L3.match(t):
            want = 2
        elif P_L2.match(t):
            want = 1
        elif P_NUM_DOT.match(t) and len(t) <= 30:
            want = 1
        if want is not None and lv != want:
            errs.append("%s 标题层级不符：%d 级应为 %d 级 —— %s" % (path.name, lv, want, t[:30]))
    prev = -1
    for i, (lv, t) in enumerate(heads):
        if i == 0 and lv != 0:
            errs.append("%s 首个正文标题不是 0 级：%s" % (path.name, t[:30]))
        if prev >= 0 and lv > prev + 1:
            errs.append("%s 标题层级断层：%d → %d（%s）" % (path.name, prev, lv, t[:30]))
        prev = lv
    nums = []
    for lv, t in heads:
        m = P_NUM.match(t)
        if m:
            nums.append(tuple(int(x) for x in m.group(1).split(".")))
    for a, b in zip(nums, nums[1:]):
        if a > b:
            warns.append("%s 编号顺序倒退：%s → %s" % (path.name, a, b))
    return errs, warns, len([h for h in heads if h[0] == 0]), len(heads)


def main(argv):
    if not argv:
        print("用法：python check_outline_tree.py <产物目录>")
        return 1
    total_e, rows = [], []
    for f in sorted(Path(argv[0]).glob("RD-*.docx")):
        e, w, n0, nt = check_doc(f)
        total_e += e
        rows.append((f.name[:6], n0, nt, len(e), w))
    for name, n0, nt, ne, w in rows:
        print("%s 一级%d 共%d 问题%d %s" % (name, n0, nt, ne, ("告警:" + "；".join(w)) if w else ""))
    if total_e:
        print("标题树门禁失败：")
        for e in total_e:
            print("  -", e)
        return 1
    print("标题树门禁通过：所有文档均有正文标题树，层级与编号一致，无重复/目录混入/表格污染")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
