# -*- coding: utf-8 -*-
"""模板载体门禁：产物的表格与“含表格的文本框”数量不得少于模板。

为什么需要（2026-11-24 定）：
`doc.tables` 只数顶层表；模板里的表单常是“文本框（w:pict）+ 文本框内嵌表（w:tbl）”。
词替换若整段合并并覆盖承载文本框的 run，会把表单整块删掉，而顶层表数、段落数都可能不变。
本门禁从 XML 比对 `w:tbl` 总数（含嵌套）与**内含表格的文本框**数量；
普通文本框数量（如图形标注）只记录不阻断，避免把已替换的旧图误判为丢失。

用法：
    python check_template_carriers.py <产物目录> --map=<template-map.json>

map 格式：
    {"029": "path/to/RD-029_模板.docx", "030": {"template": "path/to/..."}}
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def carriers(path: Path):
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    boxes = root.findall(".//" + W + "txbxContent")
    with_tbl = sum(1 for b in boxes if b.find(".//" + W + "tbl") is not None)
    return {"tbl_total": len(root.findall(".//" + W + "tbl")),
            "textboxes": len(boxes),
            "txbx_with_tbl": with_tbl}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opt = {a.split("=", 1)[0][2:]: a.split("=", 1)[1]
           for a in argv if a.startswith("--") and "=" in a}
    if not args or "map" not in opt:
        print("用法：check_template_carriers.py <产物目录> --map=<json>")
        return 2
    prod = Path(args[0]).resolve()
    tmap = json.load(open(opt["map"], encoding="utf-8"))
    errs, notes = [], []
    for f in sorted(prod.glob("RD-*.docx")):
        if f.name.startswith("~$"):
            continue
        key = f.name[3:6]
        entry = tmap.get(key)
        if entry is None:
            errs.append("%s 未登记模板（%s）" % (f.name, key))
            continue
        tpl = Path(entry["template"] if isinstance(entry, dict) else entry)
        if not tpl.exists():
            errs.append("%s 模板不存在：%s" % (f.name, tpl))
            continue
        a, b = carriers(tpl), carriers(f)
        for field in ("tbl_total", "txbx_with_tbl"):
            if b[field] < a[field]:
                errs.append("%s %s 少：产物 %d < 模板 %d（表单/嵌套表可能被整块删除）"
                            % (f.name, field, b[field], a[field]))
        notes.append("%s 表%d/%d 含表文本框%d/%d 文本框%d/%d"
                     % (f.name, b["tbl_total"], a["tbl_total"],
                        b["txbx_with_tbl"], a["txbx_with_tbl"],
                        b["textboxes"], a["textboxes"]))
    for n in notes:
        print("  ·", n)
    if errs:
        print("模板载体门禁失败：")
        for e in errs:
            print("  -", e)
        return 1
    print("模板载体门禁通过：表格（含嵌套）与含表文本框数量均不少于模板")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
