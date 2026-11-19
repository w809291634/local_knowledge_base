# -*- coding: utf-8 -*-
"""软件代码行数门禁：052 §2.1.7 必须写实际行数，且与事实台账一致。

用法：
    python check_code_lines.py <目录或文件> [--lines 12345]

判据（注册人 2026-11-19）：
1. RD-052 必须存在「软件代码行数」小节，且小节内有带「行」的阿拉伯数字；
2. 禁止占位话术：以受控的配置记录为准／见受控／待定／待确认／——；
3. 给出 --lines 时，文档数值必须与台账值完全相等（允许千分位逗号）。

统计口径登记在 pems.config.json → code_lines_policy；事实值属 S1 台账字段 `code_lines`，
并记录统计日期、提交版本、统计工具。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document

NEXT_HEAD = re.compile(r"^\s*(?:\d+(?:\.\d+)+\s|[一二三四五六七八九十]+、)")
PLACEHOLDER = ("以受控", "见受控", "待定", "待确认", "——")
VALUE = re.compile(r"(\d[\d,，]*)\s*行")


def section_text(doc, keyword: str) -> str:
    """取标题含 keyword 的小节正文（到下一个编号标题为止）。"""
    lines, inside = [], False
    for para in doc.paragraphs:
        text = para.text.strip()
        if not inside:
            if keyword in text and len(text) < 30:
                inside = True
            continue
        if NEXT_HEAD.match(text):
            break
        if text:
            lines.append(text)
    return "\n".join(lines)


def to_int(raw: str) -> int:
    return int(re.sub(r"[,，]", "", raw))


def check_doc(path: Path, expect: int):
    doc = Document(str(path))
    body = section_text(doc, "软件代码行数")
    if not body:
        return ["%s 缺「软件代码行数」小节或小节正文为空" % path.name], None
    for word in PLACEHOLDER:
        if word in body:
            return ["%s「软件代码行数」为占位话术：%s" % (path.name, body[:40])], None
    m = VALUE.search(body)
    if not m:
        return ["%s「软件代码行数」未写出带「行」的数值：%s" % (path.name, body[:40])], None
    lines = to_int(m.group(1))
    errors = []
    if lines <= 0:
        errors.append("%s「软件代码行数」数值非正：%d" % (path.name, lines))
    if expect is not None and lines != expect:
        errors.append("%s「软件代码行数」=%d，与台账 %d 不一致" % (path.name, lines, expect))
    return errors, lines


def main(argv):
    expect, targets = None, []
    i = 0
    while i < len(argv):
        if argv[i] == "--lines" and i + 1 < len(argv):
            expect = to_int(argv[i + 1])
            i += 2
            continue
        targets.append(argv[i])
        i += 1

    docs = []
    for raw in targets:
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
            errs, _ = check_doc(path, expect)
        except Exception as exc:  # 损坏/加密文件也按失败处理
            errs = ["%s 读取失败：%s" % (path.name, exc)]
        errors += errs

    if errors:
        print("软件代码行数检查失败：")
        for e in errors:
            print("  -", e)
        return 1
    print("软件代码行数检查通过：%d 份" % len(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
