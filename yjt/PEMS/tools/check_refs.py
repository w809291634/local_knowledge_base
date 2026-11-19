# -*- coding: utf-8 -*-
"""文档编号引用门禁：正文/表格不得用模板编号，052 追溯矩阵编号必须指向正确文档。

用法：
    python check_refs.py <目录或文件> [更多文件...]

判据（注册人 2026-11-19）：
1. 正文段与表格中不得出现 `QR/RD/0xx` 模板编号（页眉页脚沿用模板版号，不在扫描范围）；
2. 052 追溯矩阵「软件验证报告/文件编号」必须指向 069，「软件确认报告」必须指向 032，
   两者互串即失败；
3. 052 追溯矩阵中的文件编号必须为项目编号格式（如 052-03GSR2609010-001），不得留模板编号。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document

QR_RD = re.compile(r"QR/RD/\d{3}")
PROJECT_ID = re.compile(r"^\d{3}-[A-Za-z0-9]{8,}-\d{3}$")
MAP = (("验证报告", "069"), ("确认报告", "032"))


def doc_texts(doc):
    for para in doc.paragraphs:
        yield "段落", para.text.strip()
    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(row.cells):
                yield "表%d r%dc%d" % (ti, ri, ci), cell.text.strip()


def check_qr_rd(path, doc):
    errors = []
    for where, text in doc_texts(doc):
        if QR_RD.search(text):
            errors.append("%s %s 使用模板编号：%s" % (path.name, where, text[:40]))
    return errors


def check_trace_matrix(path, doc):
    """按「标签行 + 值行」核对 052 追溯矩阵。"""
    errors = []
    for ti, table in enumerate(doc.tables):
        rows = table.rows
        for ri, row in enumerate(rows):
            labels = [c.text.strip() for c in row.cells]
            # 追溯矩阵形态：整行每一列都是「…文件编号」标签；封面表只有首列是标签
            if not labels or not all("文件编号" in x for x in labels):
                continue
            values = [c.text.strip() for c in rows[ri + 1].cells] if ri + 1 < len(rows) else []
            for ci, label in enumerate(labels):
                if "文件编号" not in label or ci >= len(values):
                    continue
                value = values[ci]
                if not value:
                    continue
                for key, expect in MAP:
                    if key in label and expect not in value:
                        errors.append("%s 表%d「%s」填了 %s，应为 RD-%s 对应编号"
                                      % (path.name, ti, label, value, expect))
                if not PROJECT_ID.match(value) and not any(k in label for k in ("验证报告", "确认报告")):
                    errors.append("%s 表%d「%s」编号非项目编号格式：%s"
                                  % (path.name, ti, label, value))
    return errors


def check_doc(path: Path):
    doc = Document(str(path))
    errors = check_qr_rd(path, doc)
    if path.name.startswith("RD-052"):
        errors += check_trace_matrix(path, doc)
    return errors


def main(argv):
    docs = []
    for raw in argv:
        p = Path(raw)
        if p.is_dir():
            docs += [x for x in sorted(p.iterdir())
                     if x.suffix.lower() == ".docx" and x.name.startswith("RD-")]
        else:
            docs.append(p)
    if not docs:
        print("未找到待检文档")
        return 1

    errors = []
    for path in docs:
        try:
            errors += check_doc(path)
        except Exception as exc:  # 损坏/加密文件也按失败处理
            errors.append("%s 读取失败：%s" % (path.name, exc))

    if errors:
        print("文档编号引用检查失败：")
        for e in errors:
            print("  -", e)
        return 1
    print("文档编号引用检查通过：%d 份" % len(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
