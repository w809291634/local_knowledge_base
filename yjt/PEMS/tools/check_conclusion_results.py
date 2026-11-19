# -*- coding: utf-8 -*-
"""结论与结果联动门禁：032／069 有结论就必须有结果，结果不得与结论相反。

用法：
    python check_conclusion_results.py <目录或文件> [更多文件...]

判据（注册人 2026-11-19）：
1. 032／069 必须有结论章（标题含「评价」或「结论」），结论正文非空；
2. 结论正文不得是占位话术（以受控…为准／待定／待补）而无实质结论；
3. 文档存在结果列（是否通过／测试结果／结果）时：
   - 结果列全空但正文有结论 → 失败；
   - 结果列出现否定值（否／不通过／不合格／未通过）而结论为正面 → 失败；
4. 文档无结果列（如 069 按模板无结果表）时，只校验结论章，不得因此判失败。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document

CONCLUSION_HEAD = ("评价", "结论")
RESULT_COLS = ("是否通过", "测试结果", "结果")
POSITIVE = ("满足", "通过", "合格", "符合要求")
PLACEHOLDER = ("以受控", "待补", "待定", "待确认")
NEGATIVE = ("不通过", "不合格", "未通过", "否")
CN_HEAD = re.compile(r"^[一二三四五六七八九十]+、")
NUM_HEAD = re.compile(r"^\d+(?:\.\d+)*[\.、]?\s+\S")


def conclusion_text(doc) -> str:
    """收集结论章正文：中文序号章内的 6.x 子节不截断，遇到同级章才停。"""
    lines, inside, level = [], False, ""
    for para in doc.paragraphs:
        text = para.text.strip()
        # 目录条目带制表符＋页码，不当作结论标题
        if "\t" in text:
            continue
        if not inside:
            if any(k in text for k in CONCLUSION_HEAD) and len(text) < 20:
                inside = True
                level = "cn" if CN_HEAD.match(text) else "plain"
            continue
        if level == "cn" and CN_HEAD.match(text):
            break
        if level == "plain" and (CN_HEAD.match(text) or NUM_HEAD.match(text)):
            break
        if text:
            lines.append(text)
    return "\n".join(lines)


def result_values(doc):
    """返回（是否存在结果列，结果列的非空取值）。"""
    found, values = False, []
    for table in doc.tables:
        rows = table.rows
        if not rows:
            continue
        heads = [c.text.strip() for c in rows[0].cells]
        start = 1
        if not any(h in RESULT_COLS for h in heads) and len(rows) > 1:
            heads = [c.text.strip() for c in rows[1].cells]
            start = 2
        for col in RESULT_COLS:
            if col not in heads:
                continue
            found = True
            j = heads.index(col)
            for row in rows[start:]:
                cells = [c.text.strip() for c in row.cells]
                if j < len(cells) and cells[j]:
                    values.append(cells[j])
    return found, values


def check_doc(path: Path):
    doc = Document(str(path))
    errors = []
    conclusion = conclusion_text(doc)
    if not conclusion:
        return ["%s 缺结论章或结论正文为空" % path.name]

    has_positive = any(w in conclusion for w in POSITIVE)
    if not has_positive:
        errors.append("%s 结论无实质判定（应含满足／通过／合格／符合要求）：%s"
                      % (path.name, conclusion[:40]))
        for word in PLACEHOLDER:
            if word in conclusion:
                errors.append("%s 结论为占位话术：%s" % (path.name, conclusion[:40]))
                break

    found, values = result_values(doc)
    if has_positive:
        # 069 按模板无结果表，结果落结论句；032 必须有结果表
        if not found and path.name.startswith("RD-032"):
            errors.append("%s 有结论但缺结果表（是否通过／测试结果／结果）" % path.name)
        if found and not values:
            errors.append("%s 结果列全空，但结论已判定通过" % path.name)
        for v in values:
            if any(w in v for w in NEGATIVE):
                errors.append("%s 结果列出现否定值「%s」，与正面结论矛盾" % (path.name, v))
                break
    return errors


def main(argv):
    docs = []
    for raw in argv:
        p = Path(raw)
        if p.is_dir():
            docs += [x for x in sorted(p.iterdir())
                     if x.suffix.lower() == ".docx"
                     and (x.name.startswith("RD-032") or x.name.startswith("RD-069"))]
        else:
            docs.append(p)
    if not docs:
        print("未找到 RD-032／RD-069")
        return 1

    errors = []
    for path in docs:
        try:
            errors += check_doc(path)
        except Exception as exc:  # 损坏/加密文件也按失败处理
            errors.append("%s 读取失败：%s" % (path.name, exc))

    if errors:
        print("结论与结果联动检查失败：")
        for e in errors:
            print("  -", e)
        return 1
    print("结论与结果联动检查通过：%d 份" % len(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
