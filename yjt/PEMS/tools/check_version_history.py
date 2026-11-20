# -*- coding: utf-8 -*-
"""052 更新历史门禁：更新历史表必须记录「首次发布」。

用法：
    python check_version_history.py <目录或文件> [更多文件...]

判据（注册人 2026-11-20）：
1. RD-052 必须存在更新历史表（表头含「修订类型」）；
2. 表内非空数据行的「修订类型」列不得为空；
3. 更新历史中必须出现「首次发布」记录（修订类型或修订内容/变更内容描述列）。
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document

FIRST = "首次发布"
DESC_COLS = ("变更内容描述", "修订内容")


def check_doc(path: Path):
    doc = Document(str(path))
    errors, found, tables = [], False, 0
    for ti, table in enumerate(doc.tables):
        rows = table.rows
        if not rows:
            continue
        heads = [c.text.strip() for c in rows[0].cells]
        if "修订类型" not in heads:
            continue
        tables += 1
        type_j = heads.index("修订类型")
        desc_j = next((i for i, h in enumerate(heads) if h in DESC_COLS), None)
        for ri, row in enumerate(rows[1:], start=1):
            cells = [c.text.strip() for c in row.cells]
            if not any(cells):
                continue
            if not cells[type_j]:
                errors.append("%s 表%d 行%d「修订类型」为空" % (path.name, ti, ri))
            texts = [cells[type_j]] + ([cells[desc_j]] if desc_j is not None and desc_j < len(cells) else [])
            if any(FIRST in t for t in texts):
                found = True
    if not tables:
        errors.append("%s 缺更新历史表（表头需含「修订类型」）" % path.name)
    elif not found:
        errors.append("%s 更新历史缺「%s」记录" % (path.name, FIRST))
    return errors


def main(argv):
    docs = []
    for raw in argv:
        p = Path(raw)
        if p.is_dir():
            docs += [x for x in sorted(p.iterdir())
                     if x.suffix.lower() == ".docx" and x.name.startswith("RD-052")]
        else:
            docs.append(p)
    if not docs:
        print("未找到 RD-052")
        return 1

    errors = []
    for path in docs:
        try:
            errors += check_doc(path)
        except Exception as exc:  # 损坏/加密文件也按失败处理
            errors.append("%s 读取失败：%s" % (path.name, exc))

    if errors:
        print("052 更新历史检查失败：")
        for e in errors:
            print("  -", e)
        return 1
    print("052 更新历史检查通过：%d 份" % len(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
