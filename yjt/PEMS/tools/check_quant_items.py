# -*- coding: utf-8 -*-
"""052 量化项门禁：开发人员数量、时间和工作量、软件代码行数必须是实际值。

用法：
    python check_quant_items.py <目录或文件> [--lines 12345]

判据（注册人 2026-11-19）：
1. RD-052 必须存在 §2.1.5 开发人员数量、§2.1.6 时间和工作量、§2.1.7 软件代码行数三节，
   且各节正文非空；
2. 三节均不得命中占位话术：以受控…为准／以项目受控记录为准／见受控／待补／待定／待确认／——；
3. 三节必须含阿拉伯数字并带单位：人员数量带「人」、时间工作量带天/周/月/小时/人月、代码行数带「行」；
4. 给出 --lines 时，代码行数必须与台账值完全相等（允许千分位逗号）。

统计口径见 pems.config.json → code_metrics_policy；事实值属 S1 台账，
并记录统计日期、提交版本、统计工具。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document

SECTIONS = (
    ("开发人员数量", ("人",)),
    ("时间和工作量", ("天", "周", "月", "小时", "人月")),
    ("软件代码行数", ("行",)),
)
PLACEHOLDER = ("以受控", "见受控", "以项目受控记录为准", "待补", "待定", "待确认", "——")
NEXT_HEAD = re.compile(r"^\s*(?:\d+(?:\.\d+)+\s|[一二三四五六七八九十]+、)")


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


def check_doc(path: Path, expect_lines):
    doc = Document(str(path))
    errors, lines_value = [], None
    for keyword, units in SECTIONS:
        body = section_text(doc, keyword)
        if not body:
            errors.append("%s 缺「%s」小节或小节正文为空" % (path.name, keyword))
            continue
        for word in PLACEHOLDER:
            if word in body:
                idx = body.find(word)
                snippet = body[max(0, idx - 15): idx + 25]
                errors.append("%s「%s」为占位话术（命中「%s」）：%s"
                              % (path.name, keyword, word, snippet))
                break
        else:
            pattern = re.compile(r"(\d[\d,，]*)\s*(?:%s)" % "|".join(units))
            m = pattern.search(body)
            if not m:
                errors.append("%s「%s」未写出带单位的数值：%s" % (path.name, keyword, body[:40]))
            elif keyword == "软件代码行数":
                lines_value = to_int(m.group(1))
                if lines_value <= 0:
                    errors.append("%s 代码行数数值非正：%d" % (path.name, lines_value))
                elif expect_lines is not None and lines_value != expect_lines:
                    errors.append("%s 代码行数=%d，与台账 %d 不一致"
                                  % (path.name, lines_value, expect_lines))
    return errors, lines_value


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
        print("052 量化项检查失败：")
        for e in errors:
            print("  -", e)
        return 1
    print("052 量化项检查通过：%d 份" % len(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
