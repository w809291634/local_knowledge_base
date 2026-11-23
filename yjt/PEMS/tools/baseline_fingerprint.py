# -*- coding: utf-8 -*-
"""模板基线指纹（通用版）：登记每份模板的"应有结构量"，供缺失型门禁比对。

为什么需要：模板里的"表"不一定是 `w:tbl`——文本框/线条拼的表单与图在 `w:pict`(VML) 里，
只数 `doc.tables` 会把"形状被删、文字被压平"判成通过（pitfalls §104）。

用法：
    # 1) 显式映射（推荐，跨项目可控）
    python baseline_fingerprint.py --map work/baseline-map.json --out work/reports/baseline-fingerprint.json
    # 2) 自动扫描：给出模板根目录，按文件名前缀 RD-0xx 取每个编号的基线件
    python baseline_fingerprint.py --templates "…/PEMS/templates" --out …

map 格式：
    {"026": {"path": "…/RD-026_…_v3.docx", "version": "2.1_v3"}, …}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from docx import Document

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
BASELINE_HINTS = ("内容结构模板", "基线_v2", "基线", "格式档案")


def fingerprint(path: Path):
    d = Document(str(path))
    body = d.element.body
    heads = 0
    for p in d.paragraphs:
        pPr = p._p.find(W + "pPr")
        has_ol = pPr is not None and pPr.find(W + "outlineLvl") is not None
        if has_ol or (p.style.name or "").lower().startswith("heading"):
            heads += 1
    chars = sum(len(p.text.strip()) for p in d.paragraphs)
    table_chars = 0
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                table_chars += len(c.text.strip())
    chars += table_chars
    return {
        "file": path.name,
        "tables": len(d.tables),
        "table_rows": sum(len(t.rows) for t in d.tables),
        "vml_shapes": sum(1 for e in body.iter() if e.tag.split("}")[-1] == "pict"),
        "txbx": sum(1 for e in body.iter() if e.tag.split("}")[-1] == "txbxContent"),
        "inline_images": sum(1 for e in body.iter() if e.tag.split("}")[-1] == "drawing"),
        "headings": heads,
        "nonempty_paras": sum(1 for p in d.paragraphs if p.text.strip()),
        "chars": chars,
        "table_chars": table_chars,
        "sections": len(d.sections),
    }


def build_map(root: Path):
    """按 RD-0xx 前缀归组，优先取「内容结构模板 > 基线_v2 > 基线 > 格式档案」。"""
    groups = {}
    for p in root.rglob("RD-0*.docx"):
        if p.name.startswith("~$"):
            continue
        key = p.name[3:6]
        if not key.isdigit():
            continue
        rank = next((i for i, h in enumerate(BASELINE_HINTS) if h in p.name), len(BASELINE_HINTS))
        if key not in groups or rank < groups[key][0]:
            groups[key] = (rank, p)
    return {k: {"path": str(v[1]), "version": v[1].parent.name} for k, v in sorted(groups.items())}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--map")
    ap.add_argument("--templates")
    ap.add_argument("--out", default="baseline-fingerprint.json")
    a = ap.parse_args(argv)

    if a.map:
        raw = json.load(open(a.map, encoding="utf-8"))
    elif a.templates:
        raw = build_map(Path(a.templates))
    else:
        print("需要 --map 或 --templates")
        return 2

    out = {}
    for k, spec in raw.items():
        p = Path(spec["path"])
        if not p.exists():
            print("缺模板：%s" % p)
            return 1
        fp = fingerprint(p)
        fp["template_version"] = spec.get("version", p.parent.name)
        out[k] = fp
        print("%-4s 表%-2d 行%-3d 形状%-2d 图%-2d 标题%-2d 段%-4d 表内字%-4d 节%d"
              % (k, fp["tables"], fp["table_rows"], fp["vml_shapes"], fp["inline_images"],
                 fp["headings"], fp["nonempty_paras"], fp["table_chars"], fp["sections"]))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
