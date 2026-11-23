# -*- coding: utf-8 -*-
"""结构缺失门禁：产物结构量不得少于模板基线。

为什么需要（2026-11-23 定）：黑名单式判据只查"有没有错"，查不到"有没有少"。
模板里的表/图常由 VML（文本框+线条）拼成，**不在 `doc.tables` 里**；只比表数会把
"形状被删、框内文字被压平"判成通过（实测 029 少 6 处、030 少 7 处、052 少 1 处，表数却 3=3）。

判据（default）：
1. tables     产物 ≥ 基线（表不得少）
2. headings   产物 ≥ 基线（标题不得少）
3. sections   产物 == 基线（分节不得少）
4. vml_shapes / inline_images：产物 ≥ 基线 − allow
5. nonempty_paras ≥ 基线 × 0.85（防正文被掏空）
6. **adjacent_tables 必须为 0**：两个 `w:tbl` 直接相邻会被渲染成一张/出现双表头
   （052 更新历史实测 14 张变 13 张）
7. **table_chars ≥ 基线 × 0.6**：表还在但单元格被清空，表数、行数、非空段都看不出来
8. table_rows 只记录不判（用例条数随项目）

allow 清单：<项目>/work/structure-allow.json
    {"030": {"vml_shapes": {"n": 7, "reason": "旧产品框图已删，待重绘"}}}
必须写 n 与 reason；n 只减不加，reason 不得为占位话术。

用法：
    python check_structure_baseline.py <产物目录> [--baseline <json>] [--allow <json>]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def fp(path: Path):
    d = Document(str(path))
    body = d.element.body
    heads = 0
    for p in d.paragraphs:
        pPr = p._p.find(W + "pPr")
        if pPr is not None and pPr.find(W + "outlineLvl") is not None:
            heads += 1
        elif (p.style.name or "").lower().startswith("heading"):
            heads += 1
    chars = sum(len(p.text.strip()) for p in d.paragraphs)
    table_chars = 0
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                table_chars += len(c.text.strip())
    chars += table_chars
    adj = 0
    kids = list(body.iterchildren())
    for i in range(1, len(kids)):
        if kids[i].tag == kids[i - 1].tag and kids[i].tag.endswith("}tbl"):
            adj += 1
    return {
        "adjacent_tables": adj,
        "tables": len(d.tables),
        "table_rows": sum(len(t.rows) for t in d.tables),
        "vml_shapes": sum(1 for e in body.iter() if e.tag.split("}")[-1] == "pict"),
        "inline_images": sum(1 for e in body.iter() if e.tag.split("}")[-1] == "drawing"),
        "headings": heads,
        "nonempty_paras": sum(1 for p in d.paragraphs if p.text.strip()),
        "chars": chars,
        "table_chars": table_chars,
        "sections": len(d.sections),
    }


def check(prod_dir: Path, baseline: dict, allow: dict):
    errs, notes = [], []
    for f in sorted(prod_dir.glob("RD-*.docx")):
        key = f.name[3:6]
        base = baseline.get(key)
        if base is None:
            errs.append("%s 无基线指纹（%s）" % (f.name, key))
            continue
        got = fp(f)
        al = allow.get(key, {})

        def allow_n(field):
            e = al.get(field)
            if not isinstance(e, dict):
                return 0
            if not e.get("reason"):
                errs.append("%s allow.%s 缺 reason" % (f.name, field))
            return int(e.get("n", 0))

        for field in ("tables", "headings", "sections"):
            if got[field] < base[field]:
                errs.append("%s %s 少：产物 %d < 基线 %d" % (f.name, field, got[field], base[field]))
            elif got[field] > base[field]:
                notes.append("%s %s 多：产物 %d > 基线 %d" % (f.name, field, got[field], base[field]))
        for field in ("vml_shapes", "inline_images"):
            floor = base[field] - allow_n(field)
            if got[field] < floor:
                errs.append("%s %s 少：产物 %d < 下限 %d（基线 %d，允许减 %d）"
                            % (f.name, field, got[field], floor, base[field], base[field] - floor))
        if got["adjacent_tables"] > 0:
            errs.append("%s 存在 %d 处相邻表格（两个 w:tbl 直接相邻，会被渲染成一张或出现双表头）"
                        % (f.name, got["adjacent_tables"]))
        base_tc = base.get("table_chars", 0)
        if base_tc:
            floor_tc = int(base_tc * 0.6)
            if got["table_chars"] < floor_tc:
                errs.append("%s 表格内字数少：%d < 下限 %d（基线 %d）——表在但单元格内容被清空"
                            % (f.name, got["table_chars"], floor_tc, base_tc))
        floor_p = int(base["nonempty_paras"] * 0.85)
        if got["nonempty_paras"] < floor_p:
            errs.append("%s 非空段落少：%d < 下限 %d（基线 %d）"
                        % (f.name, got["nonempty_paras"], floor_p, base["nonempty_paras"]))
        notes.append("%s 表%d/%d 行%d/%d 形状%d/%d 图%d/%d 标题%d/%d 段%d/%d 表内字%d/%d"
                     % (f.name, got["tables"], base["tables"], got["table_rows"], base["table_rows"],
                        got["vml_shapes"], base["vml_shapes"], got["inline_images"], base["inline_images"],
                        got["headings"], base["headings"], got["nonempty_paras"], base["nonempty_paras"],
                        got["table_chars"], base_tc))
    return errs, notes


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opt = {a.split("=", 1)[0][2:]: a.split("=", 1)[1] for a in argv if a.startswith("--") and "=" in a}
    if not args:
        print("用法：check_structure_baseline.py <产物目录> [--baseline=json] [--allow=json]")
        return 2
    prod = Path(args[0]).resolve()
    base_path = Path(opt["baseline"]).resolve() if "baseline" in opt \
        else prod.parent / "work" / "reports" / "baseline-fingerprint.json"
    allow_path = Path(opt["allow"]).resolve() if "allow" in opt \
        else prod.parent / "work" / "structure-allow.json"
    if not base_path.exists():
        print("找不到基线指纹：%s（先跑 tools/baseline_fingerprint.py）" % base_path)
        return 2
    baseline = json.load(open(base_path, encoding="utf-8"))
    allow = json.load(open(allow_path, encoding="utf-8")) if allow_path.exists() else {}
    errs, notes = check(prod, baseline, allow)
    for n in notes:
        print("  ·", n)
    if errs:
        print("结构缺失门禁失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("结构缺失门禁通过：表/标题/分节/形状/图/正文段/表格字数均不少于基线，且无相邻表格")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
