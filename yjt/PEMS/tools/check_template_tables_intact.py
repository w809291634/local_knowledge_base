# -*- coding: utf-8 -*-
"""模板原样表门禁：核对"必须与模板保持一致"的表，逐项比对结构与格式。

与其它门禁的分工：
- `check_structure_baseline.py` 管"数量有没有少"（含 VML 形状）；
- 本门禁管"这几张表有没有被改动"——不是"跳过不改"，而是**正校验等于模板**。

判据来源：`reference-document-format-and-diagram-requirements.md`
  「分类规则 -- 封面」第九条（封面信息表）、
  「表格边框、对齐、列宽与单元格要求」第一条例外（RD-029 第九章表单、RD-030 开发计划表）、
  「分类规则 -- 字体与版式」字体统一例外。

清单：work/template-tables.json
    {"tables": [{"scope":"*"/"029", "name":…, "marker":"表内文字特征",
                 "compare":["rows","cols","borders","grid","shd","fonts"]}]}

用法：
    python check_template_tables_intact.py <产物目录> [--spec=json] [--map=json]
产物目录同级需有 work/reports/baseline-fingerprint.json 所在的项目结构，
模板路径从 --map（baseline-map.json）取。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

SIDES = ("top", "left", "bottom", "right", "insideH", "insideV")


def _text(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def _find_table(doc, marker):
    for t in doc.tables:
        if marker in _text(t._tbl):
            return t
    return None


def sig(t, allow_fill=()):
    tblPr = t._tbl.find(qn("w:tblPr"))
    borders, grid_len, shd = {}, [], []
    if tblPr is not None:
        bd = tblPr.find(qn("w:tblBorders"))
        if bd is None:
            borders = {s: None for s in SIDES}
        else:
            for s in SIDES:
                e = bd.find(qn("w:" + s))
                borders[s] = None if e is None else [e.get(qn("w:val")), e.get(qn("w:sz"))]
        gw = tblPr.find(qn("w:tblW"))
        grid_len = gw.get(qn("w:w")) if gw is not None else None
    grid = []
    tg = t._tbl.find(qn("w:tblGrid"))
    if tg is not None:
        grid = [c.get(qn("w:w")) for c in tg.findall(qn("w:gridCol"))]
    for tc in t._tbl.iter(qn("w:tc")):
        tcPr = tc.find(qn("w:tcPr"))
        sh = tcPr.find(qn("w:shd")) if tcPr is not None else None
        shd.append(None if sh is None else (sh.get(qn("w:fill")) or "").upper())
    fonts = set()
    for r in t._tbl.iter(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        if rPr is None:
            continue
        rf = rPr.find(qn("w:rFonts"))
        sz = rPr.find(qn("w:sz"))
        ea = rf.get(qn("w:eastAsia")) if rf is not None else None
        if ea or sz is not None:
            fonts.add((ea, sz.get(qn("w:val")) if sz is not None else None))
    # 字体按"生效值"归一：继承(None)解析为该表显式字体的众数（经验库 §34）
    if fonts:
        explicit = [f[0] for f in fonts if f[0]]
        if explicit:
            dom = max(set(explicit), key=explicit.count)
            fonts = {(f[0] or dom, f[1]) for f in fonts}
    texts = []
    for r in t.rows[1:]:
        cells = [c.text.strip() for c in r.cells]
        if allow_fill and cells and cells[0] in allow_fill:
            cells = [cells[0]] + ["<允许填写>"] * max(0, len(cells) - 1)
        texts.append(cells)
    return {
        "text": texts,
        "rows": len(t.rows),
        "cols": len(t.columns),
        "borders": borders,
        "grid": grid,
        "shd": shd,
        "fonts": sorted(fonts, key=lambda x: (str(x[0]), str(x[1]))),
        "tableW": grid_len,
    }


def diff(a, b, fields):
    out = []
    for f in fields:
        if a.get(f) != b.get(f):
            out.append("%s：产物 %s ≠ 模板 %s" % (f, a.get(f), b.get(f)))
    return out


def main(argv):
    args = [x for x in argv if not x.startswith("--")]
    opt = {x.split("=", 1)[0][2:]: x.split("=", 1)[1] for x in argv if x.startswith("--") and "=" in x}
    if not args:
        print("用法：check_template_tables_intact.py <产物目录> [--spec=json] [--map=json]")
        return 2
    prod = Path(args[0]).resolve()
    root = prod.parent
    spec_p = Path(opt["spec"]).resolve() if "spec" in opt else root / "work" / "template-tables.json"
    map_p = Path(opt["map"]).resolve() if "map" in opt else root / "work" / "baseline-map.json"
    if not spec_p.exists() or not map_p.exists():
        print("缺清单或模板映射：%s / %s" % (spec_p, map_p))
        return 2
    spec = json.load(open(spec_p, encoding="utf-8"))["tables"]
    tmap = json.load(open(map_p, encoding="utf-8"))

    errs, notes = [], []
    for f in sorted(prod.glob("RD-*.docx")):
        key = f.name[3:6]
        if key not in tmap:
            continue
        tpl = Document(tmap[key]["path"])
        doc = Document(str(f))
        for rule in spec:
            if rule["scope"] not in ("*", key):
                continue
            mt = _find_table(tpl, rule["marker"])
            md = _find_table(doc, rule["marker"])
            if mt is None:
                notes.append("%s 模板无「%s」，跳过" % (key, rule["name"]))
                continue
            if md is None:
                errs.append("%s 缺「%s」（模板有、产物无）" % (f.name, rule["name"]))
                continue
            af = tuple(rule.get("allow_fill", ()))
            d = diff(sig(md, af), sig(mt, af),
                     rule.get("compare", ["rows", "cols", "borders", "grid", "shd"]))
            if d:
                errs.append("%s「%s」与模板不一致：\n      - %s"
                            % (f.name, rule["name"], "\n      - ".join(d)))
            else:
                notes.append("%s「%s」与模板一致" % (key, rule["name"]))
    for n in notes:
        print("  ·", n)
    if errs:
        print("模板原样表门禁失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("模板原样表门禁通过：封面表、029 第九章表单、030 开发计划表均与模板一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
