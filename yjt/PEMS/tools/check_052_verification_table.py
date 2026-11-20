# -*- coding: utf-8 -*-
"""052 §2.5.6 验证报告表 ↔ 069 用例表一致性门禁。

用法：
    python check_052_verification_table.py <目录或文件...>
    目录时自动配对 RD-052 与 RD-069；也可直接传 052 与 069 两个文件。

判据（pems.config.json → pairing_rules.052_verification_table）：
1. 052 必须存在表头含「测试功能或项目名称」「测试结果」「是/否通过」的表；
2. 数据行数 = 069 三张用例表数据行之和；
3. 逐行「序号」= 069 用例编号、「测试功能或项目名称」= 069 测试项目名称、
   「测试类别」与 069 三表类别（单元/集成/系统）一致；
4. 「测试结果」逐行非空；「是/否通过」必须为「是」。
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document

CATS = ["单元测试", "集成测试", "系统测试"]


def read_069(path: Path):
    doc = Document(str(path))
    items, ti = [], 0
    for table in doc.tables:
        rows = table.rows
        hi = None
        for ri, row in enumerate(rows[:3]):
            heads = [c.text.strip() for c in row.cells]
            if "用例编号" in heads and "测试项目名称" in heads:
                hi = ri
                break
        if hi is None:
            continue
        cat = CATS[ti] if ti < len(CATS) else "测试"
        ti += 1
        for row in rows[hi + 1:]:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                items.append((cells[0], cat, cells[1]))
    return items


def check(p052: Path, p069: Path):
    errors = []
    doc = Document(str(p052))
    target = None
    for table in doc.tables:
        rows = table.rows
        if not rows:
            continue
        heads = [c.text.strip() for c in rows[0].cells]
        if "测试功能或项目名称" in heads and "测试结果" in heads:
            target = table
            break
    if target is None:
        return ["%s 缺 §2.5.6 验证报告表（表头需含「测试功能或项目名称」「测试结果」）" % p052.name]

    rows069 = read_069(p069)
    if not rows069:
        return ["%s 未读到用例表" % p069.name]

    heads = [c.text.strip() for c in target.rows[0].cells]
    try:
        j_no = heads.index("序号")
        j_cat = heads.index("测试类别")
        j_name = heads.index("测试功能或项目名称")
        j_res = heads.index("测试结果")
        j_ok = heads.index("是/否通过")
    except ValueError:
        return ["%s 验证报告表缺列：序号/测试类别/测试功能或项目名称/测试结果/是/否通过" % p052.name]

    data = [r for r in target.rows[1:] if any(c.text.strip() for c in r.cells)]
    if len(data) != len(rows069):
        errors.append("%s 验证报告表 %d 行，069 用例 %d 条，行数不一致"
                      % (p052.name, len(data), len(rows069)))

    for i, (row, (no, cat, name)) in enumerate(zip(data, rows069), start=2):
        cells = [c.text.strip() for c in row.cells]
        if cells[j_no] != no:
            errors.append("%s 表行%d 序号「%s」≠ 069「%s」" % (p052.name, i, cells[j_no], no))
        if cells[j_cat] != cat:
            errors.append("%s 表行%d 类别「%s」≠ 069「%s」" % (p052.name, i, cells[j_cat], cat))
        if cells[j_name] != name:
            errors.append("%s 表行%d 名称「%s」≠ 069「%s」" % (p052.name, i, cells[j_name], name))
        if not cells[j_res]:
            errors.append("%s 表行%d「测试结果」为空" % (p052.name, i))
        if cells[j_ok] != "是":
            errors.append("%s 表行%d「是/否通过」应为「是」，实际「%s」"
                          % (p052.name, i, cells[j_ok]))
    return errors


def main(argv):
    docs = []
    for raw in argv:
        p = Path(raw)
        if p.is_dir():
            docs += [x for x in sorted(p.iterdir())
                     if x.suffix.lower() == ".docx" and x.name.startswith(("RD-052", "RD-069"))]
        else:
            docs.append(p)
    p052 = next((x for x in docs if x.name.startswith("RD-052")), None)
    p069 = next((x for x in docs if x.name.startswith("RD-069")), None)
    if p052 is None or p069 is None:
        print("未找到 RD-052 与 RD-069 配对")
        return 1
    errors = check(p052, p069)
    if errors:
        print("052 验证报告表检查失败：")
        for e in errors:
            print("  -", e)
        return 1
    print("052 验证报告表检查通过：1 份（与 069 逐条一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
