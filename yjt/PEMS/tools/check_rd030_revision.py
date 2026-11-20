# -*- coding: utf-8 -*-
"""RD-030 修订记录表门禁。

用法：
    python check_rd030_revision.py <目录或文件> [更多文件...]

判据（注册人 2026-11-20 定）：
1. RD-030 必须存在修订记录表（表头含「变更原因」与「对应硬件版本」）；
2. 表只保留表头 + 1 行数据（2 行），不保留多余空行；
3. 数据行为 `V1`｜`首次发布`｜`首次发布`｜软件发布日期（20xx-xx-xx）｜责任人空｜硬件版本空；
4. 表格必须为固定布局（w:tblLayout=fixed），tblGrid 总宽 ≤ 版心可用宽度 9072 dxa；
   否则 Word 会自动压窄列宽，把 `V1` 与日期折行。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

WIDTH_LIMIT = 9072
DATE_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")


def check_doc(path: Path):
    doc = Document(str(path))
    errors = []
    target = None
    for table in doc.tables:
        rows = table.rows
        if not rows:
            continue
        heads = [c.text.strip() for c in rows[0].cells]
        if "变更原因" in heads and "对应硬件版本" in heads:
            target = table
            break
    if target is None:
        errors.append("%s 缺修订记录表（表头需含「变更原因」「对应硬件版本」）" % path.name)
        return errors

    rows = target.rows
    if len(rows) != 2:
        errors.append("%s 修订记录表应为 2 行（表头+1 行首次发布），实际 %d 行"
                      % (path.name, len(rows)))
    if len(rows) >= 2:
        cells = [c.text.strip() for c in rows[1].cells]
        if len(cells) >= 6:
            if cells[0] != "V1":
                errors.append("%s 修订记录第 1 列应为「V1」，实际「%s」" % (path.name, cells[0]))
            for j, name in ((1, "变更原因"), (2, "变更内容")):
                if "首次发布" not in cells[j]:
                    errors.append("%s 修订记录「%s」应为「首次发布」，实际「%s」"
                                  % (path.name, name, cells[j]))
            if not DATE_RE.match(cells[3]):
                errors.append("%s 修订记录「变更日期」应为 20xx-xx-xx，实际「%s」"
                              % (path.name, cells[3]))

    tbl = target._tbl
    layout = tbl.tblPr.find(qn("w:tblLayout"))
    if layout is None or layout.get(qn("w:type")) != "fixed":
        errors.append("%s 修订记录表未设固定布局（w:tblLayout=fixed）" % path.name)
    grid = tbl.tblGrid
    widths = [int(g.get(qn("w:w")) or 0) for g in grid.findall(qn("w:gridCol"))]
    if sum(widths) > WIDTH_LIMIT:
        errors.append("%s 修订记录表总宽 %d 超过版心 %d，易折行"
                      % (path.name, sum(widths), WIDTH_LIMIT))
    return errors


def main(argv):
    docs = []
    for raw in argv:
        p = Path(raw)
        if p.is_dir():
            docs += [x for x in sorted(p.iterdir())
                     if x.suffix.lower() == ".docx" and x.name.startswith("RD-030")]
        else:
            docs.append(p)
    if not docs:
        print("未找到 RD-030")
        return 1

    errors = []
    for path in docs:
        try:
            errors += check_doc(path)
        except Exception as exc:
            errors.append("%s 读取失败：%s" % (path.name, exc))

    if errors:
        print("030 修订记录表检查失败：")
        for e in errors:
            print("  -", e)
        return 1
    print("030 修订记录表检查通过：%d 份" % len(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
