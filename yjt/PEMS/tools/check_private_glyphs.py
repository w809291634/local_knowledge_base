# -*- coding: utf-8 -*-
"""私有区字形门禁：正文不得残留 Wingdings/Symbol 私有区字符。

背景（2026-11-24）：RD-029 模板的项目符号是 U+F07A（Wingdings 私有区），
宋体没有该字形，导出 PDF 后行首只剩缩进、看不到圆点。此类字符无法靠“字体统一”修好，
必须在生成阶段替换为可见符号（如 ●／•）或真正的列表编号。

判据：扫描 word/document.xml 的所有 w:t，出现 U+E000~U+F8FF 即失败（封面/眉脚同样适用）。
用法：python check_private_glyphs.py <产物目录>
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def scan(path: Path):
    errs = []
    with zipfile.ZipFile(path) as z:
        for part in z.namelist():
            if not (part.startswith("word/") and part.endswith(".xml")):
                continue
            try:
                root = etree.fromstring(z.read(part))
            except Exception:
                continue
            for t in root.iter(W + "t"):
                txt = t.text or ""
                bad = [c for c in txt if 0xE000 <= ord(c) <= 0xF8FF]
                if bad:
                    errs.append("%s %s 含私有区字符 %s：%s"
                                % (path.name, part,
                                   "、".join("U+%04X" % ord(c) for c in bad[:4]),
                                   txt.strip()[:30]))
    return errs


def main(argv):
    if not argv:
        print("用法：check_private_glyphs.py <产物目录>")
        return 2
    root = Path(argv[0]).resolve()
    total = []
    for f in sorted(root.glob("RD-*.docx")):
        if f.name.startswith("~$"):
            continue
        total += scan(f)
    if total:
        print("私有区字形门禁失败：")
        for e in total:
            print("  -", e)
        return 1
    print("私有区字形门禁通过：未发现 Wings/Symbol 私有区字符")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
