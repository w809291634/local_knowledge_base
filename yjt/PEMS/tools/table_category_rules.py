# -*- coding: utf-8 -*-
"""表分类合并门禁（注册人 2026-11-21 定）。

规则（见 reference-document-format-and-diagram-requirements.md「分组列纵向合并要求」）：
1. RD-026 测试计划表：必须有「测试类别」列，单元/集成/系统三组按大类纵向合并
   （每组首行 vMerge=restart，续行 vMerge=continue 且文字为空）。
2. RD-032 / RD-068 / RD-069：大类用独立三表表达，任何表不得出现「测试类别」列。
3. RD-052 §2.5.6：固定四列（测试类别/测试功能或项目名称/测试结果/是否通过），不设序号；
   仅「测试类别」列允许 vMerge；表头行必须有 w:tblHeader；除末行外每行段落必须有 keepNext。

用法：
    python table_category_rules.py <目录或文件...>
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

CATS = ["单元测试", "集成测试", "系统测试"]


def cells_of(tr):
    """返回 [(tc, 起始列, 跨列数, vMerge值或None, 文本)]"""
    out, col = [], 0
    for tc in tr.findall(qn("w:tc")):
        span, vm = 1, None
        tcPr = tc.find(qn("w:tcPr"))
        if tcPr is not None:
            gs = tcPr.find(qn("w:gridSpan"))
            if gs is not None:
                span = int(gs.get(qn("w:val")) or 1)
            v = tcPr.find(qn("w:vMerge"))
            if v is not None:
                vm = v.get(qn("w:val")) or "continue"
        text = "".join(t.text or "" for t in tc.iter(qn("w:t"))).strip()
        out.append((tc, col, span, vm, text))
        col += span
    return out


def table_header(tbl):
    trs = tbl._tbl.findall(qn("w:tr"))
    if not trs:
        return []
    return [c[4] for c in cells_of(trs[0])]


def find_table(doc, *must):
    for tbl in doc.tables:
        heads = table_header(tbl)
        if all(m in heads for m in must):
            return tbl, heads
    return None, []


def check_026(path: Path):
    errs = []
    doc = Document(str(path))
    tbl, heads = find_table(doc, "测试类别", "验证条款")
    if tbl is None:
        return ["%s 缺「测试类别」列（测试计划表应按大类分组）" % path.name]
    j = heads.index("测试类别")
    trs = tbl._tbl.findall(qn("w:tr"))[1:]
    groups, cur = [], None
    for k, tr in enumerate(trs):
        cells = {c[1]: c for c in cells_of(tr)}
        if j not in cells:
            errs.append("%s 表行%d 缺测试类别单元格" % (path.name, k + 2))
            continue
        _, _, _, vm, text = cells[j]
        if text:
            cur = text
            groups.append([text, 1, vm])
        elif vm == "continue" and groups:
            groups[-1][1] += 1
        else:
            errs.append("%s 表行%d 类别为空且未合并" % (path.name, k + 2))
    seq = [g[0] for g in groups]
    if seq != CATS:
        errs.append("%s 测试类别顺序/取值应%s，实际%s" % (path.name, CATS, seq))
    for name, n, vm in groups:
        if vm != "restart":
            errs.append("%s「%s」组首行缺 vMerge=restart" % (path.name, name))
        if n < 1:
            errs.append("%s「%s」组无数据行" % (path.name, name))
    return errs


def check_no_category(path: Path):
    """用例表（含用例编号/测试项目名称）不得带类别列；032「四、测试结果」汇总表不受此限。"""
    errs = []
    doc = Document(str(path))
    for i, tbl in enumerate(doc.tables):
        heads = table_header(tbl)
        is_case_table = "用例编号" in heads or "测试项目名称" in heads
        if is_case_table and "测试类别" in heads:
            errs.append("%s 表%d 用例表出现「测试类别」列（应用三张独立表）" % (path.name, i + 1))
    return errs


def check_052(path: Path):
    errs = []
    doc = Document(str(path))
    tbl, heads = find_table(doc, "测试功能或项目名称", "测试结果")
    if tbl is None:
        return ["%s 缺 §2.5.6 验证报告表" % path.name]
    expect = ["测试类别", "测试功能或项目名称", "测试结果", "是否通过"]
    if heads != expect:
        errs.append("%s 验证报告表表头应为%s，实际%s" % (path.name, expect, heads))
    if "序号" in heads:
        errs.append("%s 验证报告表不应出现「序号」列" % path.name)
    trs = tbl._tbl.findall(qn("w:tr"))
    trPr = trs[0].find(qn("w:trPr")) if trs else None
    if trPr is None or trPr.find(qn("w:tblHeader")) is None:
        errs.append("%s 验证报告表头缺 tblHeader（跨页不重复）" % path.name)
    if "测试类别" in heads:
        j = heads.index("测试类别")
        for k, tr in enumerate(trs[1:]):
            cells = {c[1]: c for c in cells_of(tr)}
            if j in cells and cells[j][3] not in (None, "restart", "continue"):
                errs.append("%s 表行%d 类别 vMerge 值异常" % (path.name, k + 2))
            for col, c in cells.items():
                if col != j and c[3] is not None:
                    errs.append("%s 表行%d 第%d列残留 vMerge（只允许类别列合并）"
                                % (path.name, k + 2, col + 1))
    for k, tr in enumerate(trs[:-1]):
        for tc in tr.findall(qn("w:tc")):
            for p in tc.findall(qn("w:p")):
                pPr = p.find(qn("w:pPr"))
                if pPr is None or pPr.find(qn("w:keepNext")) is None:
                    errs.append("%s 表行%d 缺 keepNext（易在页底拆表）" % (path.name, k + 1))
                    break
            else:
                continue
            break
    return errs


def check(paths):
    errs = []
    for raw in paths:
        p = Path(raw)
        files = [p] if p.is_file() else [x for x in sorted(p.iterdir()) if x.suffix.lower() == ".docx"]
        for f in files:
            n = f.name
            if n.startswith("RD-026"):
                errs += check_026(f)
            elif n.startswith(("RD-032", "RD-068", "RD-069")):
                errs += check_no_category(f)
            elif n.startswith("RD-052"):
                errs += check_052(f)
    return errs


def main(argv):
    errs = check(argv)
    if errs:
        print("表分类合并门禁失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("表分类合并门禁通过：026 类别合并 / 032-068-069 无类别列 / 052 四列无序号")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
